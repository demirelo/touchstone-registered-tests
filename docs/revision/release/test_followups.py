"""Tests for followups.py: deterministic packing, the manifest check, forbidden paths and the records digest."""
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "followup3"))
import followups as F  # noqa: E402
import replication_extract as RE  # noqa: E402


def _src(tmp_path, name="s"):
    s = tmp_path / name; (s / "a").mkdir(parents=True)
    (s / "a" / "r.json").write_text('{"x": 1}'); (s / "b.txt").write_text("b"); (s / "analysis.json").write_text("{}")
    return s


def test_build_is_deterministic_and_checks(tmp_path):
    s = _src(tmp_path); (tmp_path / "o1").mkdir(); (tmp_path / "o2").mkdir()
    d1 = F.build("arc", [(s, "x/s")], tmp_path / "o1"); d2 = F.build("arc", [(s, "x/s")], tmp_path / "o2")
    assert d1.read_bytes() == d2.read_bytes()
    assert F.check(d1) == []
    with tarfile.open(d1, "r:gz") as tf:
        m = json.loads(tf.extractfile("arc/MANIFEST.json").read())
        assert all(t.uid == 0 and t.uname == "" and t.mtime == F.MTIME for t in tf)
    assert set(m["files"]) == {"arc/x/s/a/r.json", "arc/x/s/b.txt", "arc/x/s/analysis.json"}


def test_records_digest_matches_the_extract(tmp_path):
    s = _src(tmp_path)
    assert F.records_digest(s) == RE.records_digest(s)


def test_check_finds_a_changed_member(tmp_path):
    s = _src(tmp_path); d = F.build("arc", [(s, "s")], tmp_path)
    with tarfile.open(d, "r:gz") as tf:
        members = [(m, tf.extractfile(m).read()) for m in tf]
    bad = tmp_path / "bad.tar.gz"
    with tarfile.open(bad, "w:gz") as tf:
        for m, b in members:
            if m.name.endswith("b.txt"):
                b = b"changed"; m.size = len(b)
            tf.addfile(m, io.BytesIO(b))
    assert any("b.txt" in p for p in F.check(bad))


@pytest.mark.parametrize("bad", ["sealed", "mac_diag"])
def test_refuses_forbidden_paths(tmp_path, bad):
    s = _src(tmp_path); (s / bad).mkdir(); (s / bad / "f").write_text("x")
    with pytest.raises(ValueError):
        F.build("arc", [(s, "s")], tmp_path)


def test_refuses_a_symlink(tmp_path):
    s = _src(tmp_path); (s / "link").symlink_to(s / "b.txt")
    with pytest.raises(ValueError):
        F.build("arc", [(s, "s")], tmp_path)


def test_spec_never_names_a_forbidden_folder():
    for parts in F.SPEC.values():
        for src, arc in parts:
            assert not any(p in F.FORBIDDEN for p in src.parts + Path(arc).parts)
