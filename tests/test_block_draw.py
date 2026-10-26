"""Block reader (design 7.3): attestation verified against explorer headers, header chain from A to H + 6, two-source
agreement. Offline: tests/fixtures/btc_headers.json holds 11 real mainnet headers from height 971818, the lowest Bitcoin
attestation of docs/lock-2026-10-17.txt.ots, recorded with
    python: urllib.request.urlopen("https://blockstream.info/api/block-height/<h>"), then ".../api/block/<hash>/header";
tests/fixtures/lock_ots_info.txt is `ots info docs/lock-2026-10-17.txt.ots`."""
import json
from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"
H = json.loads((FIX / "btc_headers.json").read_text())["headers"]
A = H[0]["height"]
INFO = (FIX / "lock_ots_info.txt").read_text()


def raw(i):
    return bytes.fromhex(H[i]["header"])


def fake_fetch(tip=None, at=None, headers=None, missing=()):
    """Both sources serve the fixture unless overridden: at[source][height] -> hash, headers[hash] -> hex."""
    by_h = {h["height"]: h["hash"] for h in H}; by_hash = {h["hash"]: h["header"] for h in H}
    by_hash.update(headers or {})

    def fetch(source, path):
        if path == "blocks/tip/height":
            return str((tip or {}).get(source, A + 10))
        if path.startswith("block-height/"):
            h = int(path.split("/")[1])
            if h in missing:
                raise KeyError(path)
            return ((at or {}).get(source) or {}).get(h, by_h.get(h))
        if path.startswith("block/") and path.endswith("/header"):
            return by_hash[path.split("/")[1]]
        raise KeyError(path)
    return fetch


def test_header_hash_matches_fixture():
    from scripts.block_draw import header_hash
    assert all(header_hash(raw(i)) == H[i]["hash"] for i in range(len(H)))


def test_verify_chain_accepts_fixture():
    from scripts.block_draw import verify_chain
    assert verify_chain([raw(i) for i in range(11)], H[0]["hash"]) == [h["hash"] for h in H]


def test_verify_chain_rejects_tampered_link_bits_and_first_hash():
    from scripts.block_draw import verify_chain
    hs = [raw(i) for i in range(11)]
    with pytest.raises(ValueError):
        verify_chain(hs, H[1]["hash"])
    with pytest.raises(ValueError):
        verify_chain([hs[0], hs[2]] + hs[3:], H[0]["hash"])
    bad = bytearray(hs[3]); bad[72:76] = (0x207fffff).to_bytes(4, "little")     # easier target: the hash no longer matches its successor
    with pytest.raises(ValueError):
        verify_chain(hs[:3] + [bytes(bad)] + hs[4:], H[0]["hash"])
    weak = bytearray(hs[0]); weak[76:80] = b"\0\0\0\0"                             # nonce changed: proof of work fails
    with pytest.raises(ValueError):
        verify_chain([bytes(weak)], __import__("scripts.block_draw", fromlist=["header_hash"]).header_hash(bytes(weak)))


def test_attestations_parse():
    from scripts.block_draw import attestations
    att = attestations(INFO)
    assert att[0][0] == A and att == sorted(att) and len(att[0][1]) == 64


def test_anchor_is_verified_attestation_and_merkle_root():
    from scripts.block_draw import anchor, merkle_root
    a = anchor(INFO, fake_fetch())
    assert a == {"status": "verified", "height": A, "merkle_root": merkle_root(raw(0)), "hash": H[0]["hash"], "lower_attestations": [], "lower_headers": []}


def test_anchor_skips_failed_lower_attestation():
    from scripts.block_draw import anchor
    info = f"    verify BitcoinBlockHeaderAttestation({A - 1})\n    # Bitcoin block merkle root {'ab' * 32}\n" + INFO
    f = fake_fetch(at={"blockstream": {A - 1: H[1]["hash"]}, "mempool": {A - 1: H[1]["hash"]}})
    a = anchor(info, f)
    assert a["height"] == A and a["lower_attestations"] == [{"height": A - 1, "attested_root": "ab" * 32, "hash": H[1]["hash"], "header": H[1]["header"]}]


def test_anchor_refuses_without_bitcoin_attestation():
    from scripts.block_draw import anchor
    with pytest.raises(ValueError):
        anchor("    verify PendingAttestation('https://a.example')\n", fake_fetch())


def anchor_rec():
    from scripts.block_draw import merkle_root
    return {"status": "verified", "height": A, "merkle_root": merkle_root(raw(0)), "hash": H[0]["hash"]}


def test_target_height():
    from scripts.block_draw import target_height
    assert target_height(100) == 244 and target_height(100, 4) == 104


def test_read_final_waits_on_disagreement_or_low_tip():
    from scripts.block_draw import read_final
    assert read_final(anchor_rec(), fake_fetch(tip={"mempool": A + 9}), offset=4)["status"] == "wait"
    assert read_final(anchor_rec(), fake_fetch(at={"mempool": {A + 4: H[5]["hash"]}}), offset=4)["status"] == "wait"


def test_read_final_returns_agreed_hash():
    from scripts.block_draw import read_final
    r = read_final(anchor_rec(), fake_fetch(), offset=4)
    assert r["status"] == "final" and r["height"] == A + 4 and r["hash"] == H[4]["hash"] and len(r["headers"]) == 11


def test_read_final_rejects_unrelated_chain():
    from scripts.block_draw import read_final
    other = {s: {A: H[1]["hash"]} for s in ("blockstream", "mempool")}     # A served as another valid header
    with pytest.raises(ValueError):
        read_final(anchor_rec(), fake_fetch(at={"blockstream": {**other["blockstream"]}}), offset=4)


def test_read_final_rejects_explorers_agreeing_on_other_anchor():
    from scripts.block_draw import read_final
    both = {s: {A: H[1]["hash"]} for s in ("blockstream", "mempool")}
    with pytest.raises(ValueError):
        read_final(anchor_rec(), fake_fetch(at=both), offset=4)


def test_read_final_rejects_truncated_chain():
    from scripts.block_draw import read_final
    with pytest.raises((ValueError, KeyError)):
        read_final(anchor_rec(), fake_fetch(missing={A + 10}), offset=4)


def test_read_final_rejects_h_position_mismatch():
    from scripts.block_draw import read_final
    both = {s: {A + 4: H[5]["hash"]} for s in ("blockstream", "mempool")}
    with pytest.raises(ValueError):
        read_final(anchor_rec(), fake_fetch(at=both), offset=4)


def test_file_digest_and_protocol_binding():
    from scripts.block_draw import check_protocol, file_digest
    proto = (FIX / "lock-2026-10-17.txt").read_bytes()
    assert file_digest(INFO) == __import__("hashlib").sha256(proto).hexdigest()
    check_protocol(INFO, proto)
    with pytest.raises(ValueError):
        check_protocol(INFO, proto + b"changed")
    with pytest.raises(ValueError):
        file_digest("no digest line\n")
