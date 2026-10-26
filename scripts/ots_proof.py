"""A minimal parser of OpenTimestamps detached proofs (final review K1). It reads the file digest and walks the timestamp
tree, applying each operation (append, prepend, sha256, sha1, ripemd160, reverse, hexlify) to the message, so each Bitcoin
attestation's commitment is computed from the digest rather than read from a listing. A Bitcoin attestation's commitment
is the block's Merkle root in internal byte order; it is returned in display order (as block_draw.merkle_root)."""
from __future__ import annotations

import hashlib

MAGIC = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"
BITCOIN = bytes.fromhex("0588960d73d71901")
PENDING = bytes.fromhex("83dfe30d2ef90c8e")
MAX_DEPTH = 256


class ProofError(ValueError):
    pass


class _R:
    def __init__(self, b: bytes):
        self.b, self.i = b, 0

    def byte(self) -> int:
        if self.i >= len(self.b):
            raise ProofError("the proof ends early")
        self.i += 1
        return self.b[self.i - 1]

    def take(self, n: int) -> bytes:
        if self.i + n > len(self.b):
            raise ProofError("the proof ends early")
        self.i += n
        return self.b[self.i - n:self.i]

    def varuint(self) -> int:
        v, shift = 0, 0
        while True:
            c = self.byte(); v |= (c & 0x7F) << shift; shift += 7
            if not c & 0x80:
                return v
            if shift > 63:
                raise ProofError("varuint too long")

    def varbytes(self, limit: int = 8192) -> bytes:
        n = self.varuint()
        if n > limit:
            raise ProofError("varbytes too long")
        return self.take(n)


def _op(tag: int, r: _R, msg: bytes) -> bytes:
    if tag == 0xF0:
        return msg + r.varbytes()
    if tag == 0xF1:
        return r.varbytes() + msg
    if tag == 0x08:
        return hashlib.sha256(msg).digest()
    if tag == 0x02:
        return hashlib.sha1(msg).digest()
    if tag == 0x03:
        try:
            return hashlib.new("ripemd160", msg).digest()
        except ValueError:
            raise ProofError("ripemd160 is unavailable")
    if tag == 0xF2:
        return msg[::-1]
    if tag == 0xF3:
        return msg.hex().encode()
    raise ProofError(f"unknown operation 0x{tag:02x}")


def _walk(r: _R, msg: bytes, out: dict, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise ProofError("the timestamp tree is too deep")

    def branch(tag: int):
        if tag == 0x00:
            kind, payload = r.take(8), r.varbytes()
            if kind == BITCOIN:
                out["attestations"].append((_R(payload).varuint(), msg[::-1].hex()))
            elif kind == PENDING:
                out["pending"] += 1
        else:
            _walk(r, _op(tag, r, msg), out, depth + 1)
    tag = r.byte()
    while tag == 0xFF:
        branch(r.byte()); tag = r.byte()
    branch(tag)


def parse(proof: bytes) -> dict:
    r = _R(bytes(proof))
    if r.take(len(MAGIC)) != MAGIC:
        raise ProofError("not an OpenTimestamps proof")
    if r.varuint() != 1:
        raise ProofError("unsupported proof version")
    if r.byte() != 0x08:
        raise ProofError("the file digest is not SHA-256")
    digest = r.take(32); out = {"digest": digest.hex(), "attestations": [], "pending": 0}
    _walk(r, digest, out)
    if r.i != len(r.b):
        raise ProofError("trailing bytes after the timestamp")
    out["attestations"] = sorted(set(out["attestations"]))
    return out
