import json
import pytest
from sim.sealed import BUNDLE_FILES, bundle_hash, verify_bundle, patch_log, verify_patches, demoted_cells, load_bundle, final_eval_seeds
from sim.locked import load_locked, seeds


def make_bundle(root):
    s = root / "sealed"; (s / "h2").mkdir(parents=True); (s / "patches").mkdir()
    (s / "README.md").write_text("bundle\n"); (s / "h1_prompt.txt").write_text("You are a provider.\n")
    (s / "h2" / "family.py").write_text("from sim.policies.families import D2 as H2\nCONTAINMENT = 'contains D2 through an embedding'\n")
    (s / "h2" / "containment.md").write_text("H2 contains D2.\n")
    (s / "final_eval_seeds.json").write_text(json.dumps(list(range(5000, 5040))))
    (s / "identity_salt.hex").write_text("00" * 32 + "\n"); (s / "b1_check.json").write_text(json.dumps({"B1": "pass"}))
    return s


def test_bundle_hash_is_content_addressed_and_ignores_patches_and_bytecode(tmp_path):
    s = make_bundle(tmp_path); h = bundle_hash(s)
    assert len(h) == 64 and set(BUNDLE_FILES) <= {str(p.relative_to(s)) for p in s.rglob("*") if p.is_file()}
    (s / "patches" / "x.diff").write_text("d\n"); assert bundle_hash(s) == h
    (s / "h2" / "__pycache__").mkdir(); (s / "h2" / "__pycache__" / "family.cpython-312.pyc").write_bytes(b"\x00"); assert bundle_hash(s) == h
    (s / "h1_prompt.txt").write_text("changed\n"); assert bundle_hash(s) != h


def test_verify_and_load_bundle_and_seed_fallback(tmp_path, monkeypatch):
    import importlib
    s = make_bundle(tmp_path); lk = dict(load_locked(), sealed_bundle_sha256=bundle_hash(s))
    verify_bundle(s, lk)
    with pytest.raises(ValueError):
        verify_bundle(s, dict(lk, sealed_bundle_sha256="00" * 32))
    b = load_bundle(s, lk)
    assert b.h1_prompt.startswith("You are") and b.final_eval_seeds == list(range(5000, 5040)) and b.h2_module.H2.name == "D2" and b.salt_hex == "00" * 32
    assert final_eval_seeds(s) == list(range(5000, 5040))
    monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(s)); import sim.registry as reg; importlib.reload(reg)
    assert seeds(lk, "final_eval") == list(range(5000, 5040))
    with pytest.raises(ValueError):
        seeds(dict(lk, sealed_bundle_sha256="11" * 32), "final_eval")
    assert patch_log(s) == {} and verify_patches(s) == [] and demoted_cells(s) == set()
    (s / "patches" / "a.diff").write_text("a\n")
    assert verify_patches(s) != []
