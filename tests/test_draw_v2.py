"""Draw to instances and the single H4 decision (operations plan Task 7). Draw records are built by the block reader itself
from the 11 recorded mainnet headers of tests/fixtures (offsets below 144 because only 11 headers exist; the default is
144); the protocol bytes are docs/lock-2026-10-17.txt, the file the recorded proof commits to."""
import copy
import functools
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from tests.test_block_draw import A, H, INFO, fake_fetch, raw

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = (ROOT / "docs" / "lock-2026-10-17.txt").read_bytes()
TOY = Path(__file__).resolve().parent / "fixtures" / "h4_toy"


@pytest.fixture(autouse=True)
def fast_calibration(monkeypatch):
    import sim.instances as INST
    monkeypatch.setattr(INST, "calibrated", lambda cfg, rho=0.2, beta=0.05: cfg)


def _record(info=INFO, offset=4, fetch=None):
    from scripts.block_draw import anchor, check_protocol, read_final
    f = fetch or fake_fetch()
    r = read_final(anchor(info, f), f, offset=offset)
    assert r["status"] == "final"
    r["protocol_sha256"] = check_protocol(info, PROTOCOL)
    return json.loads(json.dumps(r))


def test_valid_record_is_accepted():
    from scripts.draw_v2 import instances
    inst = instances(_record(), PROTOCOL, INFO, published_height=A + 1, offset=4)
    assert inst["root"] == H[4]["hash"] and inst["height"] == A + 4 and inst["confirmatory"] is True


def test_instances_follow_generator_and_streams(monkeypatch):
    import sim.instances as INST
    from scripts.draw_v2 import instances
    from sim.records import cfg_to_dict
    inst = instances(_record(), PROTOCOL, INFO, published_height=A + 1, offset=4); root = inst["root"]
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
    inst2 = instances(_record(), PROTOCOL, INFO, published_height=A + 1, offset=4)
    assert list(inst2["markets"]) == [f"fresh{i}" for i in range(6)] and inst2["markets"]["fresh2"]["stream_index"] == 6


def _two_attestations():
    from scripts.block_draw import merkle_root
    return INFO + f"\n    verify BitcoinBlockHeaderAttestation({A + 2})\n    # Bitcoin block merkle root {merkle_root(raw(2))}\n"


def _lower_bogus():
    return f"    verify BitcoinBlockHeaderAttestation({A - 1})\n    # Bitcoin block merkle root {'ab' * 32}\n" + INFO


def _fetch_lower():
    return fake_fetch(at={"blockstream": {A - 1: H[1]["hash"]}, "mempool": {A - 1: H[1]["hash"]}})


def test_substituted_draw_is_refused():
    from scripts.block_draw import anchor, check_protocol, read_final
    from scripts.draw_v2 import Refused, instances
    good = _record()
    cases = {}
    r = copy.deepcopy(good); r["anchor"].update(height=A + 1, hash=H[1]["hash"]); cases["unrelated anchor with the digest rewritten"] = (r, INFO, 4)
    r = copy.deepcopy(good); r["height"] = A + 5; cases["H != A + offset"] = (r, INFO, 4)
    r = copy.deepcopy(good); r["headers"][2], r["headers"][3] = r["headers"][3], r["headers"][2]; cases["broken header link"] = (r, INFO, 4)
    r = copy.deepcopy(good); r["hash"] = H[5]["hash"]; cases["hash mismatch"] = (r, INFO, 4)
    r = copy.deepcopy(good); r["answers_at_h"]["mempool"] = H[5]["hash"]; cases["disagreeing answers"] = (r, INFO, 4)
    r = copy.deepcopy(good); r["tips"]["mempool"] = A + 9; cases["tips below H + 6"] = (r, INFO, 4)
    r = copy.deepcopy(good); r["protocol_sha256"] = "0" * 64; cases["digest field differs"] = (r, INFO, 4)
    two = _two_attestations(); f = fake_fetch()
    later = {"status": "verified", "height": A + 2, "merkle_root": __import__("scripts.block_draw", fromlist=["x"]).merkle_root(raw(2)), "hash": H[2]["hash"], "lower_attestations": []}
    rl = read_final(later, f, offset=2); rl["protocol_sha256"] = check_protocol(two, PROTOCOL)
    cases["draw on the later of two valid attestations"] = (json.loads(json.dumps(rl)), two, 2)
    low = _record(_lower_bogus(), 4, _fetch_lower()); assert low["anchor"]["lower_attestations"]
    r = copy.deepcopy(low); r["anchor"]["lower_attestations"] = []; cases["lower attestation missing"] = (r, _lower_bogus(), 4)
    for name, (rec, info, off) in cases.items():
        with pytest.raises(Refused):
            instances(rec, PROTOCOL, info, published_height=A + 1, offset=off)
        assert name
    assert instances(_record(two, 2), PROTOCOL, two, published_height=A + 1, offset=2)["height"] == A + 2      # the lowest of the two passes
    assert instances(low, PROTOCOL, _lower_bogus(), published_height=A + 1, offset=4)["root"] == H[4]["hash"]
    with pytest.raises(Refused):
        instances(good, b"another protocol", INFO, published_height=A + 1, offset=4)


def test_unchanged_reader_output_is_accepted(tmp_path, monkeypatch):
    import scripts.block_draw as BD
    from scripts.draw_v2 import Refused, instances
    monkeypatch.setattr(BD, "http_fetch", fake_fetch())
    monkeypatch.setattr(BD, "read_final", functools.partial(BD.read_final, offset=4))
    monkeypatch.setattr(BD.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": INFO})())
    proto = tmp_path / "protocol.txt"; proto.write_bytes(PROTOCOL); out = tmp_path / "draw.json"
    BD.main(["--ots", "x.ots", "--protocol", str(proto), "--out", str(out)])
    rec = json.loads(out.read_text())
    assert instances(rec, PROTOCOL, INFO, published_height=A + 1, offset=4)["root"] == rec["hash"]
    rec.pop("protocol_sha256")
    with pytest.raises(Refused):
        instances(rec, PROTOCOL, INFO, published_height=A + 1, offset=4)


def test_late_publication_is_nonconfirmatory():
    from scripts.draw_v2 import instances
    assert instances(_record(), PROTOCOL, INFO, published_height=None, offset=4)["confirmatory"] is False
    assert instances(_record(), PROTOCOL, INFO, published_height=A + 4, offset=4)["confirmatory"] is False
    assert instances(_record(), PROTOCOL, INFO, published_height=A + 3, offset=4)["confirmatory"] is True


def test_seeds_equal_an_independent_derivation():
    from scripts.draw_v2 import instances
    inst = instances(_record(), PROTOCOL, INFO, published_height=A + 1, offset=4); root = inst["root"]
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


def test_cli_writes_both_files(tmp_path):
    import yaml
    from scripts.draw_v2 import main
    d, sha = _bundle(tmp_path)
    draw = tmp_path / "draw.json"; draw.write_text(json.dumps(_record()))
    proto = tmp_path / "protocol.txt"; proto.write_bytes(PROTOCOL); info = tmp_path / "info.txt"; info.write_text(INFO)
    out = tmp_path / "out" / "draw"
    assert main(["--instances", "--draw", str(draw), "--protocol", str(proto), "--ots-info", str(info), "--published-height", str(A + 1),
                 "--offset", "4", "--out", str(out)]) == 0
    assert json.loads((out / "instances.json").read_text())["root"] == H[4]["hash"]
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
    assert main(["--h4-decision", "--protocol", str(py), "--out", str(out)]) == 1                  # a rerun without the bundle cannot reverse it
    assert main(["--h4-decision", "--protocol", str(py), "--bundle", str(d), "--out", str(out)]) == 0   # an identical rerun is accepted
    assert (out / "h4.json").read_text() == first


def test_k7_an_exclusion_cannot_be_reversed(tmp_path):
    import yaml
    from scripts.draw_v2 import main
    d, sha = _bundle(tmp_path); out = tmp_path / "draw"
    py = tmp_path / "protocol-v2.yaml"; py.write_text(yaml.safe_dump({"h4": {"commit": "a" * 40, "bundle_sha256": sha}}))
    assert main(["--h4-decision", "--protocol", str(py), "--out", str(out)]) == 0 and json.loads((out / "h4.json").read_text())["loaded"] is False
    assert main(["--h4-decision", "--protocol", str(py), "--bundle", str(d), "--out", str(out)]) == 1
