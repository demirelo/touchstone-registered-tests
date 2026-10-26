"""The OpenTimestamps proof parser (final review K1): operations applied from the file digest to each attested commitment,
checked on the real proof of docs/lock-2026-10-17.txt against the recorded mainnet header at its Bitcoin attestation."""
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"


def test_real_proof_commits_the_file_to_the_mainnet_merkle_root():
    from scripts.block_draw import attestations, merkle_root
    from scripts.ots_proof import parse
    p = parse((ROOT / "docs" / "lock-2026-10-17.txt.ots").read_bytes())
    assert p["digest"] == hashlib.sha256((ROOT / "docs" / "lock-2026-10-17.txt").read_bytes()).hexdigest()
    h = json.loads((FIX / "btc_headers.json").read_text())["headers"]
    A = h[0]["height"]; root = merkle_root(bytes.fromhex(h[0]["header"]))
    assert (A, root) in p["attestations"]
    assert sorted(p["attestations"]) == attestations((FIX / "lock_ots_info.txt").read_text())      # agrees with `ots info`


def test_corrupt_or_foreign_proofs_are_refused():
    from scripts.ots_proof import ProofError, parse
    raw = (ROOT / "docs" / "lock-2026-10-17.txt.ots").read_bytes()
    with pytest.raises(ProofError):
        parse(b"not a proof")
    with pytest.raises(ProofError):
        parse(raw[:-3])
