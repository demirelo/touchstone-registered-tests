"""Atomic records with provenance and upstream hashes (plan Task 11)."""
import json

import pytest


def test_write_read_atomic_and_truncated(tmp_path):
    from sim.records_v2 import read, write
    p = tmp_path / "a" / "r.json"
    write(p, {"x": 1})
    assert read(p) == {"x": 1} and not list(p.parent.glob("*.tmp"))
    p.write_text('{"x": ')
    assert read(p) is None and read(tmp_path / "missing.json") is None


def test_validate_provenance_and_upstream(tmp_path):
    from sim.records_v2 import sha_file, validate, write
    up = tmp_path / "up.json"; write(up, {"a": 1})
    job = {"provenance": {"git_commit": "c", "runner_sha256": "r"}}
    rec = {"stage": "reference", "provenance": dict(job["provenance"]), "upstream": {"u": sha_file(up)}}
    validate(job, "reference", rec, {"u": up})
    with pytest.raises(ValueError):
        validate(job, "search", rec, {"u": up})
    with pytest.raises(ValueError):
        validate({"provenance": {"git_commit": "other"}}, "reference", rec, {"u": up})
    write(up, {"a": 2})
    with pytest.raises(ValueError):
        validate(job, "reference", rec, {"u": up})
