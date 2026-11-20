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
    m1 = C.build(root, ["plan.md", "sim/a.py"], head, required=[])
    m2 = C.build(root, ["sim/a.py", "plan.md"], head, required=[])
    assert m1 == m2 and json.loads(m1)["commit"] == head
    (root / "manifest.json").write_bytes(m1)
    assert C.verify(root, root / "manifest.json", required=[]) == []
    (root / "plan.md").write_text("changed\n")
    assert any("plan.md" in p for p in C.verify(root, root / "manifest.json", required=[]))


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
    (root / "manifest.json").write_bytes(C.build(root, ["plan.md"], head, required=[]))
    C.require(root, root / "manifest.json", required=[])
    (root / "plan.md").write_text("changed\n")
    with pytest.raises(SystemExit):
        C.require(root, root / "manifest.json", required=[])


# ---- review rep-impl-r1 (Sol 1, Astra 1): a required file set, the import closure, the frozen inputs ------------------

def test_build_and_verify_refuse_a_manifest_without_a_required_file(tmp_path):
    root, head = _repo(tmp_path)
    with pytest.raises(SystemExit):
        C.build(root, [], head, required=["plan.md"])
    (root / "m.json").write_bytes(C.build(root, ["plan.md"], head, required=[]))   # an old, partial manifest
    (root / "m2.json").write_text(json.dumps({"commit": head, "files": {}}))       # an empty manifest
    assert any("required" in p for p in C.verify(root, root / "m2.json", required=["plan.md"]))
    assert C.verify(root, root / "m.json", required=["plan.md"]) == []


def test_import_closure_follows_imports_inside_functions(tmp_path):
    root, head = _repo(tmp_path)
    d = root / "docs"; d.mkdir()
    (d / "a.py").write_text("import json\n\ndef f():\n    from b import g\n    return g\n")
    (d / "b.py").write_text("import c\n")
    (d / "c.py").write_text("from sim import a\n")
    assert C.import_closure(root, ["docs/a.py"], [d]) == {"docs/a.py", "docs/b.py", "docs/c.py"}
    with pytest.raises(SystemExit):
        C.build(root, ["docs/a.py", "docs/b.py"], head, required=[], search=[d])


def test_the_real_required_set_covers_the_drivers_import_closure():
    root = Path(__file__).resolve().parents[3]
    py = [f for f in C.REQUIRED if f.endswith(".py")]
    missing = C.import_closure(root, py, C.search_dirs(root)) - set(C.REQUIRED)
    assert not missing, missing
    assert all((root / f).is_file() for f in C.REQUIRED), [f for f in C.REQUIRED if not (root / f).is_file()]


def test_a_change_to_a_frozen_configuration_input_is_refused(tmp_path, monkeypatch):
    root, head = _repo(tmp_path)
    monkeypatch.delenv("TOUCHSTONE_LOCKED", raising=False)
    (root / "experiments").mkdir(); (root / "experiments" / "locked.yaml").write_text("a: 1\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "commit.gpgsign=false", "commit", "-q", "-m", "d"], check=True)
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert C.frozen_problems(root, head) == []
    (root / "experiments" / "locked.yaml").write_text("a: 2\n")
    assert any("experiments/locked.yaml" in p for p in C.frozen_problems(root, head))


# ---- review rep-impl-r2 (Sol 1, Astra 1): scripts run as subprocesses, the records the drivers read, git errors -------

def test_import_closure_follows_scripts_named_in_string_literals(tmp_path):
    root, head = _repo(tmp_path)
    d = root / "docs"; d.mkdir()
    (d / "a.py").write_text("import subprocess\nsubprocess.run(['python', str(HERE / 'child.py')])\n")
    (d / "child.py").write_text("import json\n")
    assert C.import_closure(root, ["docs/a.py"], [d]) == {"docs/a.py", "docs/child.py"}


def test_the_real_required_set_lists_the_runner_up_recheck_record_and_the_memory_task():
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "docs/revision/followup2"))
    import runnerup_v2
    assert str(runnerup_v2.LOG.relative_to(root)) in C.REQUIRED
    assert "docs/revision/churn/churn_memory.py" in C.REQUIRED


def test_freeze_check_refuses_an_unknown_commit(tmp_path, monkeypatch):
    root, head = _repo(tmp_path)
    monkeypatch.delenv("TOUCHSTONE_LOCKED", raising=False)
    assert any("git" in p for p in C.frozen_problems(root, "0" * 40))
