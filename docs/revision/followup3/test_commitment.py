"""Tests for the commitment manifest and the run-time freeze check (plan section 5)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import commitment as C  # noqa: E402


def _repo(tmp_path):
    def git(*a):
        subprocess.run(["git", "-C", str(tmp_path), *a], check=True, capture_output=True)
    git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
    for d in ("sim", "scripts"):
        (tmp_path / d).mkdir(); (tmp_path / d / "a.py").write_text("x = 1\n")
    (tmp_path / "plan.md").write_text("plan\n")
    git("add", "."); git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "c")
    return tmp_path, subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def test_manifest_bytes_are_deterministic_and_verify(tmp_path):
    root, head = _repo(tmp_path)
    m1 = C.build(root, ["plan.md", "sim/a.py"], head)
    m2 = C.build(root, ["sim/a.py", "plan.md"], head)
    assert m1 == m2 and json.loads(m1)["commit"] == head
    (root / "manifest.json").write_bytes(m1)
    assert C.verify(root, root / "manifest.json") == []
    (root / "plan.md").write_text("changed\n")
    assert any("plan.md" in p for p in C.verify(root, root / "manifest.json"))


def test_freeze_check_refuses_a_working_tree_change_an_untracked_file_and_an_override(tmp_path, monkeypatch):
    root, head = _repo(tmp_path)
    monkeypatch.delenv("TOUCHSTONE_LOCKED", raising=False)
    assert C.frozen_problems(root, head) == []
    (root / "sim" / "a.py").write_text("x = 2\n")
    assert any("sim" in p for p in C.frozen_problems(root, head))
    (root / "sim" / "a.py").write_text("x = 1\n")
    (root / "scripts" / "new.py").write_text("y = 1\n")
    assert any("untracked" in p for p in C.frozen_problems(root, head))
    (root / "scripts" / "new.py").unlink()
    monkeypatch.setenv("TOUCHSTONE_LOCKED", "1")
    assert any("TOUCHSTONE_LOCKED" in p for p in C.frozen_problems(root, head))


def test_require_raises_on_any_problem(tmp_path, monkeypatch):
    root, head = _repo(tmp_path)
    monkeypatch.delenv("TOUCHSTONE_LOCKED", raising=False)
    (root / "manifest.json").write_bytes(C.build(root, ["plan.md"], head))
    C.require(root, root / "manifest.json")
    (root / "plan.md").write_text("changed\n")
    with pytest.raises(SystemExit):
        C.require(root, root / "manifest.json")
