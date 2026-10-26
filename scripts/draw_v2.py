"""From the final block read to the fresh instances, and the single H4 decision (design 5.3, 7; operations plan Task 7).
--instances re-checks the block reader's final record offline against the committed upgraded proof (its bytes, parsed by
scripts/ots_proof.py) and the protocol bytes: the proof commits to these bytes; the anchor is the proof's lowest valid
attestation (every lower one is recorded on one continuous chain into A, with a header that does not carry its root); H = A + 144; the stored headers link from A to H + 6 with
their proof of work; both explorers' tips reach H + 6 and their answers at H agree with the hash. It then derives the six
fresh instances, 200 evaluation seeds per market, and the salt hash from the root, and labels the draw nonconfirmatory
when the protocol was published at or after H. --h4-decision loads the sealed bundle once, through the loader, against
the protocol's commitment; every evaluation pod enforces that one decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.block_draw import header_hash, merkle_root, verify_chain  # noqa: E402
from scripts.ots_proof import ProofError, parse  # noqa: E402
from sim import instances as INST  # noqa: E402
from sim.h4_loader import H4Source, load  # noqa: E402
from sim.records import cfg_to_dict  # noqa: E402

LABELS = ("headline",) + tuple(f"fresh{i}" for i in range(6))


class Refused(Exception):
    pass


def _require(ok: bool, msg: str) -> None:
    if not ok:
        raise Refused(msg)


def verify_draw(draw: dict, protocol_bytes: bytes, proof_bytes: bytes, offset: int = 144, depth: int = 6) -> None:
    _require(draw.get("status") == "final", "the draw record is not final")
    try:
        proof = parse(proof_bytes)
    except ProofError as e:
        raise Refused(f"proof: {e}")
    digest = hashlib.sha256(protocol_bytes).hexdigest()
    _require(proof["digest"] == digest, "the proof does not commit to these protocol bytes")
    _require(draw.get("protocol_sha256") == digest, "the draw record's protocol digest is missing or differs from the proof's")
    anc = draw.get("anchor") or {}; att = proof["attestations"]
    _require((anc.get("height"), anc.get("merkle_root")) in att, "the anchor is not one of the proof's attestations")
    A = int(anc["height"]); raws = [bytes.fromhex(h) for h in draw.get("headers") or []]
    lower = [(h, r) for h, r in att if h < A]; recorded = {int(x["height"]): x for x in anc.get("lower_attestations") or []}
    prefix = [bytes.fromhex(h) for h in anc.get("lower_headers") or []]
    if lower:
        lo = lower[0][0]
        _require(len(prefix) == A - lo, "the headers from the lowest attestation to the anchor are not all recorded")
        try:
            full = verify_chain(prefix + raws, header_hash(prefix[0]))
        except (ValueError, IndexError) as e:
            raise Refused(f"the chain from the lowest attestation to the anchor does not link: {e}")
        _require(full[A - lo] == anc["hash"], "the anchor is not on the chain from the lowest attestation")
        for h, root in lower:
            x = recorded.get(h)
            _require(x is not None and x.get("attested_root") == root and full[h - lo] == x.get("hash"), f"the lower attestation at {h} is not recorded on the chain")
            _require(merkle_root(prefix[h - lo]) != root, f"the lower attestation at {h} is valid: the anchor is not the lowest")
    else:
        _require(not recorded and not prefix, "lower attestations are recorded that the proof does not hold")
    Ht = A + int(offset)
    _require(int(draw.get("height", -1)) == Ht, f"H is {draw.get('height')}, not A + {offset} = {Ht}")
    _require(len(raws) == int(offset) + int(depth) + 1, "the stored headers do not span A to H + depth")
    try:
        chain = verify_chain(raws, anc["hash"])
    except ValueError as e:
        raise Refused(f"header chain: {e}")
    _require(merkle_root(raws[0]) == anc["merkle_root"], "the anchor header does not carry the protocol commitment")
    h = str(draw.get("hash"))
    _require(re.fullmatch(r"[0-9a-f]{64}", h) is not None and chain[int(offset)] == h, "the hash at H is not the chain's header hash at H")
    tips = draw.get("tips") or {}
    _require(len(tips) == 2 and min(int(v) for v in tips.values()) >= Ht + int(depth), "a tip is below H + depth")
    answers = draw.get("answers_at_h") or {}
    _require(len(answers) == 2 and set(answers.values()) == {h}, "the explorers' answers at H disagree with the hash")


def instances(draw: dict, protocol_bytes: bytes, proof_bytes: bytes, published_height: int | None, offset: int = 144, depth: int = 6) -> dict:
    verify_draw(draw, protocol_bytes, proof_bytes, offset, depth)
    root = draw["hash"]; Ht = int(draw["height"])
    markets = {m["label"]: {"stream_index": m["stream_index"], "rejections": m["rejections"], "cfg": cfg_to_dict(m["cfg"]),
                            "calibrated_cfg": cfg_to_dict(INST.calibrated(m["cfg"]))} for m in INST.markets(root, 6)}
    return {"root": root, "height": Ht, "markets": markets, "seeds": {m: INST.eval_seeds(root, m) for m in LABELS},
            "salt_sha256": hashlib.sha256(bytes.fromhex(INST.identity_salt_hex(root))).hexdigest(),
            "confirmatory": published_height is not None and int(published_height) < Ht, "published_height": published_height}


def h4_decision(bundle: Path | None, protocol: dict) -> dict:
    reg = protocol.get("h4")
    if not reg:
        return {"loaded": False, "reason": "no bundle is registered", "bundle_sha256": None, "h4_excluded": True, "registered_sha256": None}
    base = {"bundle_sha256": reg["bundle_sha256"], "registered_sha256": reg["bundle_sha256"]}
    if bundle is None:
        return {"loaded": False, "reason": "the bundle was not supplied", "h4_excluded": True, **base}
    src = load(Path(bundle), reg["bundle_sha256"])
    if isinstance(src, H4Source):
        return {"loaded": True, "reason": None, "h4_excluded": False, **base}
    return {"loaded": False, "reason": src.reason, "h4_excluded": True, **base}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--instances", action="store_true"); g.add_argument("--h4-decision", dest="h4_decision", action="store_true")
    ap.add_argument("--draw"); ap.add_argument("--protocol", required=True); ap.add_argument("--ots", default=None, help="the committed upgraded proof")
    ap.add_argument("--published-height", dest="published", type=int, default=None); ap.add_argument("--offset", type=int, default=144)
    ap.add_argument("--bundle", default=None); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.instances:
        if not a.ots:
            raise SystemExit("--instances needs --ots, the committed upgraded proof")
        try:
            inst = instances(json.loads(Path(a.draw).read_text()), Path(a.protocol).read_bytes(), Path(a.ots).read_bytes(), a.published, a.offset)
        except Refused as e:
            print(f"refused: {e}", file=sys.stderr)
            return 1
        (out / "instances.json").write_text(json.dumps(inst, indent=1, default=float))
        return 0
    dec = h4_decision(Path(a.bundle) if a.bundle else None, yaml.safe_load(Path(a.protocol).read_text()))
    target = out / "h4.json"
    if target.exists():                                          # the decision is made once; only an identical rerun is accepted
        if json.loads(target.read_text()) != dec:
            print(f"refused: {target} holds another decision; it is never rewritten", file=sys.stderr)
            return 1
        return 0
    target.write_text(json.dumps(dec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
