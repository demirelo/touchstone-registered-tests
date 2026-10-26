"""Draw to instances and the single H4 decision (operations plan Task 7; final review K1, K2, K7). The draw records are
built by the block reader itself from a synthetic chain mined at the regtest target whose Merkle roots are the real
commitments of OpenTimestamps proofs (tests/_chain.py), so the proof-to-protocol, proof-to-header, and lowest-anchor
bindings are all cryptographic. Offsets below 144 keep the chain short; the default is 144."""
import copy
import functools
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from tests import _chain as C

PROTOCOL = b"protocol v2 (test)\n"
OTHER = b"another protocol\n"
TOY = Path(__file__).resolve().parent / "fixtures" / "h4_toy"
S = C.START
TAG_A, TAG_B, TAG_L = b"branch-a", b"branch-b", b"branch-low"


@pytest.fixture(autouse=True)
def fast_calibration(monkeypatch):
    import sim.instances as INST
    monkeypatch.setattr(INST, "calibrated", lambda cfg, rho=0.2, beta=0.05: cfg)


@pytest.fixture(scope="module")
def world():
    """Valid attestations at S+2 (branch a) and S+4 (branch b); a bogus lower one at S+1 (branch low, not in the chain)."""
    ch = C.chain(20, {S + 2: C.commitment(PROTOCOL, TAG_A), S + 4: C.commitment(PROTOCOL, TAG_B)})
    return {"chain": ch, "proof": C.proof(PROTOCOL, [(TAG_A, S + 2)]), "two": C.proof(PROTOCOL, [(TAG_A, S + 2), (TAG_B, S + 4)]),
            "low": C.proof(PROTOCOL, [(TAG_L, S + 1), (TAG_A, S + 2)]), "other": C.proof(OTHER, [(TAG_A, S + 2)])}


def _record(w, proof, protocol=PROTOCOL, offset=4, anc=None):
    from scripts.block_draw import anchor, read_final
    from scripts.ots_proof import parse
    f = C.fetcher(w["chain"])
    a = anc or anchor(parse(proof)["attestations"], f)
    r = read_final(a, f, offset=offset)
    assert r["status"] == "final"
    r["protocol_sha256"] = hashlib.sha256(protocol).hexdigest()
    return json.loads(json.dumps(r))


def test_valid_record_is_accepted(world):
    from scripts.draw_v2 import instances
    inst = instances(_record(world, world["proof"]), PROTOCOL, world["proof"], published_height=S + 3, offset=4)
    assert inst["root"] == world["chain"][S + 6][0] and inst["height"] == S + 6 and inst["confirmatory"] is True


def test_instances_follow_generator_and_streams(world, monkeypatch):
    import sim.instances as INST
    from scripts.draw_v2 import instances
    from sim.records import cfg_to_dict
    inst = instances(_record(world, world["proof"]), PROTOCOL, world["proof"], published_height=S + 3, offset=4); root = inst["root"]
    want = INST.markets(root, 6)
    assert list(inst["markets"]) == [f"fresh{i}" for i in range(6)]
    assert [(v["stream_index"], v["rejections"], v["cfg"]) for v in inst["markets"].values()] == [(m["stream_index"], m["rejections"], cfg_to_dict(m["cfg"])) for m in want]
    assert inst["salt_sha256"] == hashlib.sha256(bytes.fromhex(INST.identity_salt_hex(root))).hexdigest()
    real = INST._draw_stream

    def limited(r, i, limit):
        if i == 2:
            raise INST.InstanceLimit("limit")
        return real(r, i, limit)
    monkeypatch.setattr(INST, "_draw_stream", limited)
    inst2 = instances(_record(world, world["proof"]), PROTOCOL, world["proof"], published_height=S + 3, offset=4)
    assert list(inst2["markets"]) == [f"fresh{i}" for i in range(6)] and inst2["markets"]["fresh2"]["stream_index"] == 6


def test_lowest_of_two_valid_attestations_and_a_rejected_lower_one(world):
    from scripts.draw_v2 import instances
    two = _record(world, world["two"], offset=2)
    assert two["anchor"]["height"] == S + 2 and instances(two, PROTOCOL, world["two"], published_height=S + 3, offset=2)["height"] == S + 4
    low = _record(world, world["low"])
    assert low["anchor"]["height"] == S + 2 and [x["height"] for x in low["anchor"]["lower_attestations"]] == [S + 1] and len(low["anchor"]["lower_headers"]) == 1
    assert instances(low, PROTOCOL, world["low"], published_height=S + 3, offset=4)["root"] == world["chain"][S + 6][0]


def test_substituted_draw_is_refused(world):
    from scripts.block_draw import merkle_root, read_final
    from scripts.draw_v2 import Refused, instances
    good = _record(world, world["proof"]); cases = {}
    r = copy.deepcopy(good); r["protocol_sha256"] = "0" * 64; cases["digest field differs"] = (r, PROTOCOL, world["proof"], 4)
    r = copy.deepcopy(good); r["protocol_sha256"] = hashlib.sha256(OTHER).hexdigest()
    cases["other protocol, both digest fields changed, with its own proof"] = (r, OTHER, world["other"], 4)
    cases["valid draw, proof of another protocol"] = (copy.deepcopy(good), PROTOCOL, world["other"], 4)
    r = copy.deepcopy(good); r["height"] = S + 7; cases["H != A + offset"] = (r, PROTOCOL, world["proof"], 4)
    r = copy.deepcopy(good); r["headers"][2], r["headers"][3] = r["headers"][3], r["headers"][2]; cases["broken header link"] = (r, PROTOCOL, world["proof"], 4)
    r = copy.deepcopy(good); r["hash"] = world["chain"][S + 7][0]; cases["hash mismatch"] = (r, PROTOCOL, world["proof"], 4)
    r = copy.deepcopy(good); r["answers_at_h"]["mempool"] = world["chain"][S + 7][0]; cases["disagreeing answers"] = (r, PROTOCOL, world["proof"], 4)
    r = copy.deepcopy(good); r["tips"]["mempool"] = S + 11; cases["tips below H + 6"] = (r, PROTOCOL, world["proof"], 4)
    raw4 = bytes.fromhex(world["chain"][S + 4][1])
    later = {"status": "verified", "height": S + 4, "merkle_root": merkle_root(raw4), "hash": world["chain"][S + 4][0], "lower_attestations": [], "lower_headers": []}
    rl = read_final(later, C.fetcher(world["chain"]), offset=2); rl["protocol_sha256"] = hashlib.sha256(PROTOCOL).hexdigest()
    cases["draw on the later of two valid attestations"] = (json.loads(json.dumps(rl)), PROTOCOL, world["two"], 2)
    low = _record(world, world["low"])
    r = copy.deepcopy(low); r["anchor"]["lower_attestations"] = []; cases["lower attestation missing"] = (r, PROTOCOL, world["low"], 4)
    r = copy.deepcopy(low); r["anchor"]["lower_headers"] = [world["chain"][S + 3][1]]
    r["anchor"]["lower_attestations"][0].update(hash=world["chain"][S + 3][0], header=world["chain"][S + 3][1]); cases["lower header from another height"] = (r, PROTOCOL, world["low"], 4)
    for name, (rec, proto, proof, off) in cases.items():
        with pytest.raises(Refused):
            instances(rec, proto, proof, published_height=S + 3, offset=off)
        assert name


def test_unchanged_reader_output_is_accepted(world, tmp_path, monkeypatch):
    import scripts.block_draw as BD
    from scripts.draw_v2 import Refused, instances
    monkeypatch.setattr(BD, "http_fetch", C.fetcher(world["chain"]))
    monkeypatch.setattr(BD, "read_final", functools.partial(BD.read_final, offset=4))
    proto = tmp_path / "protocol.txt"; proto.write_bytes(PROTOCOL); ots = tmp_path / "protocol.txt.ots"; ots.write_bytes(world["low"]); out = tmp_path / "draw.json"
    BD.main(["--ots", str(ots), "--protocol", str(proto), "--out", str(out)])
    rec = json.loads(out.read_text())
    assert instances(rec, PROTOCOL, world["low"], published_height=S + 3, offset=4)["root"] == rec["hash"]
    rec.pop("protocol_sha256")
    with pytest.raises(Refused):
        instances(rec, PROTOCOL, world["low"], published_height=S + 3, offset=4)


def test_late_publication_is_nonconfirmatory(world):
    from scripts.draw_v2 import instances
    rec = _record(world, world["proof"])
    assert instances(rec, PROTOCOL, world["proof"], published_height=None, offset=4)["confirmatory"] is False
    assert instances(rec, PROTOCOL, world["proof"], published_height=S + 6, offset=4)["confirmatory"] is False
    assert instances(rec, PROTOCOL, world["proof"], published_height=S + 5, offset=4)["confirmatory"] is True


def test_seeds_equal_an_independent_derivation(world):
    from scripts.draw_v2 import instances
    inst = instances(_record(world, world["proof"]), PROTOCOL, world["proof"], published_height=S + 3, offset=4); root = inst["root"]
    assert list(inst["seeds"]) == ["headline"] + [f"fresh{i}" for i in range(6)]
    for m, got in inst["seeds"].items():
        want, n = [], 0
        while len(want) < 200:
            d = hashlib.sha256((root + "|touchstone-v2|" + "seeds/" + m + "|" + str(n)).encode("ascii")).digest()
            v = 30_000_000 + int.from_bytes(d[:8], "big") % 10_000_000; n += 1
            if v not in want:
                want.append(v)
        assert got == want
    allv = [v for s in inst["seeds"].values() for v in s]
    assert all(30_000_000 <= v < 40_000_000 for v in allv) and not (set(allv) & (set(range(1000, 1005)) | set(range(2000, 2020)) | set(range(4000, 4020))))


def _bundle(tmp_path):
    from sim.h4_loader import bundle_sha
    d = tmp_path / "sealed2"; shutil.copytree(TOY, d); (d / "h4" / "check.json").write_text(json.dumps({"load": {"ok": True}}))
    return d, bundle_sha(d)


def test_h4_decision_loads_a_valid_bundle(tmp_path):
    from scripts.draw_v2 import h4_decision
    d, sha = _bundle(tmp_path)
    dec = h4_decision(d, {"h4": {"commit": "a" * 40, "bundle_sha256": sha}})
    assert dec == {"loaded": True, "reason": None, "bundle_sha256": sha, "h4_excluded": False, "registered_sha256": sha}


def test_h4_decision_records_exclusion(tmp_path):
    from scripts.draw_v2 import h4_decision
    d, sha = _bundle(tmp_path)
    dec = h4_decision(d, {"h4": {"commit": "a" * 40, "bundle_sha256": "0" * 64}})
    assert dec["loaded"] is False and dec["h4_excluded"] is True and "hash" in dec["reason"]
    assert h4_decision(None, {"h4": {"commit": "a" * 40, "bundle_sha256": sha}})["h4_excluded"] is True
    assert h4_decision(d, {"h4": None})["h4_excluded"] is True


def test_cli_writes_both_files(world, tmp_path):
    import yaml
    from scripts.draw_v2 import main
    d, sha = _bundle(tmp_path)
    draw = tmp_path / "draw.json"; draw.write_text(json.dumps(_record(world, world["proof"])))
    proto = tmp_path / "protocol.txt"; proto.write_bytes(PROTOCOL); ots = tmp_path / "protocol.txt.ots"; ots.write_bytes(world["proof"])
    out = tmp_path / "out" / "draw"
    assert main(["--instances", "--draw", str(draw), "--protocol", str(proto), "--ots", str(ots), "--published-height", str(S + 3),
                 "--offset", "4", "--out", str(out)]) == 0
    assert json.loads((out / "instances.json").read_text())["root"] == world["chain"][S + 6][0]
    py = tmp_path / "protocol-v2.yaml"; py.write_text(yaml.safe_dump({"h4": {"commit": "a" * 40, "bundle_sha256": sha}}))
    assert main(["--h4-decision", "--protocol", str(py), "--bundle", str(d), "--out", str(out)]) == 0
    assert json.loads((out / "h4.json").read_text())["loaded"] is True


# ---- final review K7: one H4 decision, never rewritten --------------------------------------------------------------------------

def test_k7_the_decision_is_written_once(tmp_path):
    import yaml
    from scripts.draw_v2 import main
    d, sha = _bundle(tmp_path); out = tmp_path / "draw"
    py = tmp_path / "protocol-v2.yaml"; py.write_text(yaml.safe_dump({"h4": {"commit": "a" * 40, "bundle_sha256": sha}}))
    assert main(["--h4-decision", "--protocol", str(py), "--bundle", str(d), "--out", str(out)]) == 0
    first = (out / "h4.json").read_text()
    assert json.loads(first)["loaded"] is True and json.loads(first)["registered_sha256"] == sha
    assert main(["--h4-decision", "--protocol", str(py), "--out", str(out)]) == 1
    assert main(["--h4-decision", "--protocol", str(py), "--bundle", str(d), "--out", str(out)]) == 0
    assert (out / "h4.json").read_text() == first


def test_k7_an_exclusion_cannot_be_reversed(tmp_path):
    import yaml
    from scripts.draw_v2 import main
    d, sha = _bundle(tmp_path); out = tmp_path / "draw"
    py = tmp_path / "protocol-v2.yaml"; py.write_text(yaml.safe_dump({"h4": {"commit": "a" * 40, "bundle_sha256": sha}}))
    assert main(["--h4-decision", "--protocol", str(py), "--out", str(out)]) == 0 and json.loads((out / "h4.json").read_text())["loaded"] is False
    assert main(["--h4-decision", "--protocol", str(py), "--bundle", str(d), "--out", str(out)]) == 1
