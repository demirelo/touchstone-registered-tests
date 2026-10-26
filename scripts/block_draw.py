"""The fresh draw's block reader (design 7.3). The anchor A is the lowest Bitcoin attestation of the protocol file's
OpenTimestamps proof whose block header, as served by both explorers, carries the proof's Merkle root (the commitment);
`ots verify` needs a local Bitcoin node, so this check replaces it. H = A + 144. The hash at H is final once both explorers
report a tip of at least H + 6 and agree on it, and the header chain from A to H + 6 links and carries its proof of work."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

SOURCES = ("blockstream", "mempool")
BASES = {"blockstream": "https://blockstream.info/api/", "mempool": "https://mempool.space/api/"}
DIGEST = re.compile(r"^File sha256 hash: ([0-9a-f]{64})", re.M)
ATTESTATION = re.compile(r"BitcoinBlockHeaderAttestation\((\d+)\)\s*\n\s*# Bitcoin block merkle root ([0-9a-f]{64})")


def header_hash(raw: bytes) -> str:
    return hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()


def merkle_root(raw: bytes) -> str:
    return raw[36:68][::-1].hex()


def prev_hash(raw: bytes) -> str:
    return raw[4:36][::-1].hex()


def target_from_bits(bits: int) -> int:
    exp, mant = bits >> 24, bits & 0x007FFFFF
    return mant << (8 * (exp - 3)) if exp >= 3 else mant >> (8 * (3 - exp))


def verify_chain(headers: list[bytes], first_hash: str) -> list[str]:
    out = []
    for n, raw in enumerate(headers):
        if len(raw) != 80:
            raise ValueError(f"header {n}: length {len(raw)}")
        h = header_hash(raw)
        if n == 0 and h != first_hash:
            raise ValueError("first header does not have the expected hash")
        if n > 0 and prev_hash(raw) != out[-1]:
            raise ValueError(f"header {n}: broken link")
        if int(h, 16) > target_from_bits(int.from_bytes(raw[72:76], "little")):
            raise ValueError(f"header {n}: insufficient proof of work")
        out.append(h)
    return out


def file_digest(ots_info: str) -> str:
    m = DIGEST.search(ots_info)
    if not m:
        raise ValueError("the proof listing has no file digest")
    return m.group(1)


def check_protocol(ots_info: str, protocol: bytes) -> str:
    """The proof must commit to exactly these protocol bytes."""
    d = hashlib.sha256(protocol).hexdigest()
    if file_digest(ots_info) != d:
        raise ValueError("the proof does not commit to this protocol file")
    return d


def attestations(ots_info: str) -> list[tuple[int, str]]:
    return sorted((int(h), root) for h, root in ATTESTATION.findall(ots_info))


def target_height(anchor_height: int, offset: int = 144) -> int:
    return int(anchor_height) + int(offset)


def _hash_at(fetch, height: int) -> dict:
    return {s: str(fetch(s, f"block-height/{height}")).strip() for s in SOURCES}


def _header(fetch, h: str) -> bytes:
    return bytes.fromhex(str(fetch(SOURCES[0], f"block/{h}/header")).strip())


def anchor(ots_info: str, fetch) -> dict:
    """The lowest attestation whose header (both sources agreeing on its hash) carries the attested Merkle root; every
    lower attestation it rejected is kept with the header served at its height, so the choice can be re-checked offline."""
    att = attestations(ots_info)
    if not att:
        raise ValueError("the proof has no Bitcoin attestation")
    lower = []
    for height, root in att:
        hs = _hash_at(fetch, height)
        if len(set(hs.values())) != 1:
            return {"status": "wait", "height": height, "reason": "sources disagree", "answers": hs}
        h = hs[SOURCES[0]]; raw = _header(fetch, h)
        if header_hash(raw) == h and merkle_root(raw) == root:
            return {"status": "verified", "height": height, "merkle_root": root, "hash": h, "lower_attestations": lower}
        lower.append({"height": height, "attested_root": root, "hash": h, "header": raw.hex()})
    raise ValueError("no attestation matches its block header")


def read_final(anc: dict, fetch, offset: int = 144, depth: int = 6) -> dict:
    A = int(anc["height"]); Ht = target_height(A, offset)
    tips = {s: int(str(fetch(s, "blocks/tip/height")).strip()) for s in SOURCES}
    if min(tips.values()) < Ht + depth:
        return {"status": "wait", "reason": "tip below H + depth", "tips": tips, "height": Ht}
    at_h = _hash_at(fetch, Ht)
    if len(set(at_h.values())) != 1:
        return {"status": "wait", "reason": "sources disagree at H", "answers": at_h, "height": Ht}
    at_a = _hash_at(fetch, A)
    if any(v != anc["hash"] for v in at_a.values()):
        raise ValueError(f"the sources' block at A differs from the verified anchor: {at_a}")
    raws = []
    for height in range(A, Ht + depth + 1):
        raws.append(_header(fetch, str(fetch(SOURCES[0], f"block-height/{height}")).strip()))
    if merkle_root(raws[0]) != anc["merkle_root"]:
        raise ValueError("the anchor header does not carry the protocol commitment")
    chain = verify_chain(raws, anc["hash"])
    if chain[Ht - A] != at_h[SOURCES[0]]:
        raise ValueError("the agreed hash at H is not on the verified chain")
    return {"status": "final", "height": Ht, "hash": chain[Ht - A], "anchor": anc, "headers": [r.hex() for r in raws], "tips": tips,
            "answers_at_h": at_h}


def http_fetch(source: str, path: str) -> str:
    import urllib.request
    return urllib.request.urlopen(BASES[source] + path, timeout=60).read().decode()


def main(argv=None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ots", required=True); ap.add_argument("--protocol", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--poll", type=int, default=3600)
    a = ap.parse_args(argv)
    info = subprocess.run(["uvx", "--from", "opentimestamps-client", "ots", "info", a.ots], capture_output=True, text=True, check=True).stdout
    digest = check_protocol(info, Path(a.protocol).read_bytes())
    while True:
        anc = anchor(info, http_fetch)
        if anc["status"] == "verified":
            r = read_final(anc, http_fetch)
            if r["status"] == "final":
                r["protocol_sha256"] = digest
                Path(a.out).write_text(json.dumps(r, indent=1)); print(r["height"], r["hash"]); return
        print(json.dumps(anc if anc["status"] != "verified" else r), file=sys.stderr)
        time.sleep(a.poll)


if __name__ == "__main__":
    main()
