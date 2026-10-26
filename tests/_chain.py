"""Synthetic Bitcoin headers and OpenTimestamps proofs for the draw tests (final review K1, K2). Headers are mined at the
regtest target (bits 0x207fffff, about two tries per header), and their Merkle roots are the proofs' real commitments, so
every binding the draw checks is cryptographic."""
from __future__ import annotations

import hashlib
import struct

from scripts.ots_proof import BITCOIN, MAGIC

BITS = 0x207FFFFF
START = 900_000


def _sha256d(b: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(b).digest()).digest()


def _varuint(n: int) -> bytes:
    out = b""
    while True:
        c = n & 0x7F; n >>= 7
        out += bytes([c | (0x80 if n else 0)])
        if not n:
            return out


def _varbytes(b: bytes) -> bytes:
    return _varuint(len(b)) + b


def commitment(protocol: bytes, tag: bytes) -> bytes:
    """The message an attestation on branch `tag` commits to: sha256(sha256(protocol) || tag)."""
    return hashlib.sha256(hashlib.sha256(protocol).digest() + tag).digest()


def proof(protocol: bytes, branches: list[tuple[bytes, int]]) -> bytes:
    """A detached proof with one branch per (tag, height): append(tag), sha256, Bitcoin attestation at height."""
    def branch(tag, height):
        return b"\xf0" + _varbytes(tag) + b"\x08" + b"\x00" + BITCOIN + _varbytes(_varuint(height))
    body = b"".join(b"\xff" + branch(t, h) for t, h in branches[:-1]) + branch(*branches[-1])
    return MAGIC + _varuint(1) + b"\x08" + hashlib.sha256(protocol).digest() + body


def header(prev: bytes, root: bytes, t: int) -> bytes:
    """`prev` and `root` in internal byte order."""
    for nonce in range(1 << 20):
        raw = struct.pack("<I", 0x20000000) + prev + root + struct.pack("<III", t, BITS, nonce)
        if int.from_bytes(_sha256d(raw)[::-1], "big") <= (BITS & 0x7FFFFF) << (8 * ((BITS >> 24) - 3)):
            return raw
    raise RuntimeError("no nonce found")


def chain(n: int, roots: dict, start: int = START) -> dict:
    """Heights start..start+n-1 -> (hash display hex, header hex); `roots` maps height -> commitment (internal order)."""
    out, prev = {}, b"\0" * 32
    for i in range(n):
        h = start + i; raw = header(prev, roots.get(h, hashlib.sha256(b"filler%d" % h).digest()), 1_700_000_000 + i)
        prev = _sha256d(raw); out[h] = (prev[::-1].hex(), raw.hex())
    return out


def fetcher(ch: dict, tip: int | None = None, at: dict | None = None):
    by_hash = {hx: raw for hx, raw in ch.values()}; top = max(ch)

    def fetch(source, path):
        if path == "blocks/tip/height":
            return str(tip if tip is not None else top)
        if path.startswith("block-height/"):
            h = int(path.split("/")[1])
            return ((at or {}).get(source) or {}).get(h, ch[h][0])
        if path.startswith("block/") and path.endswith("/header"):
            return by_hash[path.split("/")[1]]
        raise KeyError(path)
    return fetch
