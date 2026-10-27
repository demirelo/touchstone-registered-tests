"""The H4 session kit (operations plan Task 1): load check, smoke evaluation on development seeds, check.json inside the hash."""
import json
import shutil
from pathlib import Path

import pytest

TOY = Path(__file__).resolve().parent / "fixtures" / "h4_toy"


CRED = {"cred": {"variant": "thr", "K": 6, "M": None}}
PAYLOAD = {"defender_commit", "h4_seconds", "x7_seconds", "h4_episodes", "x7_episodes", "knobs", "controls"}


def _copy(tmp_path) -> Path:
    d = tmp_path / "sealed2"; shutil.copytree(TOY, d)
    return d


def _cred(tmp_path) -> str:
    p = tmp_path / "comparator.json"; p.write_text(json.dumps(CRED))
    return str(p)


def test_toy_bundle_passes_load_and_hash_round_trip(tmp_path, capsys):
    from scripts.h4_check import main
    from sim.h4_loader import H4Source, bundle_sha, load
    d = _copy(tmp_path)
    assert main(["--bundle", str(d), "--smoke", "--comparator", _cred(tmp_path), "--defender-commit", "abc123"]) == 0
    export = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    chk = json.loads((d / "h4" / "check.json").read_text())
    assert chk["load"]["ok"] is True and chk["load"]["constants"] == [[200, 10], [100, 20]]
    assert set(chk) >= {"load", "smoke", "scipy", "commit", "timing"} and export["bundle_sha256"] == bundle_sha(d)
    assert isinstance(load(d, export["bundle_sha256"]), H4Source)


def test_h4_check_prints_timing(tmp_path, capsys):
    from scripts.h4_check import main
    from sim.h4_loader import bundle_sha
    d = _copy(tmp_path)
    main(["--bundle", str(d), "--smoke", "--comparator", _cred(tmp_path), "--defender-commit", "abc123"])
    export = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    payload = json.loads((d / "h4" / "check.json").read_text())["timing"]
    assert set(payload) == PAYLOAD and "bundle_sha256" not in payload and payload["defender_commit"] == "abc123"
    assert export == {"bundle_sha256": bundle_sha(d), "commit": export["commit"], **payload}
    assert payload["h4_seconds"] > 0 and payload["x7_seconds"] > 0 and payload["h4_episodes"] > 0 and payload["controls"] > 0


@pytest.mark.parametrize("src,needle", [
    ("from dataclasses import replace\nfrom sim.policies.families import FAMILIES\nfrom sim.policies.identity import h3_family\n"
     "def make_family(T, L):\n    return replace(h3_family(FAMILIES['D2']), name='H4')\n", "BINARY"),
    ("from dataclasses import replace\nfrom sim.policies.families import FAMILIES\nfrom sim.policies.identity import h3_family\nBINARY = ('x', 'clip')\n"
     "def make_family(T, L):\n    return replace(h3_family(FAMILIES['D2']), name='X')\n", "H4"),
])
def test_missing_binary_or_wrong_name_fails_load_check(tmp_path, src, needle):
    from scripts.h4_check import load_check
    d = _copy(tmp_path); (d / "h4" / "family.py").write_text(src)
    r = load_check(d)
    assert r["ok"] is False and needle in r["problem"]


def test_smoke_touches_development_seeds_only(tmp_path, monkeypatch):
    import sim.instances as INST
    from scripts.h4_check import smoke
    monkeypatch.setattr(INST, "eval_seeds", lambda *a, **k: (_ for _ in ()).throw(AssertionError("reserved evaluation seeds")))
    r = smoke(_copy(tmp_path), cred=CRED["cred"])
    assert set(r) == {f"{rule}|{m}" for rule in ("F000", "F111", "C*") for m in ("dev0", "dev1")}
    dev = set(range(1000, 1005)) | set(range(2000, 2020))
    for v in r.values():
        assert set(v["train_seeds"]) | set(v["eval_seeds"]) <= dev and "gain" in v and v["train_seeds"] and v["eval_seeds"]


def test_check_json_is_inside_the_hash(tmp_path):
    from scripts.h4_check import main
    from sim.h4_loader import bundle_sha
    d = _copy(tmp_path); main(["--bundle", str(d), "--smoke", "--comparator", _cred(tmp_path), "--defender-commit", "abc123"])
    before = bundle_sha(d); p = d / "h4" / "check.json"; p.write_text(p.read_text() + " ")
    assert bundle_sha(d) != before


def test_h4_brief_allows_defender_source():
    """Design draft 7, 5.3: the sealed author may study the frozen defence; the envelope and the timing record are stated."""
    text = (Path(__file__).resolve().parents[1] / "docs" / "revision" / "h4-brief.md").read_text()
    allowed = text.split("## What you may read", 1)[1].split("##", 1)[0]
    assert "sim/mechanisms/" in allowed and "comparator.json" in allowed and "tuned" in allowed
    assert "at most 15 knobs" in text and "8 core-hours" in text and "Family.project" in text
    assert "--defender-commit" in text and "bundle_sha256" in text and "Do not read `sealed/`" in text
    forbid = next(line for line in text.splitlines() if line.startswith("Do not read"))
    assert "sim/mechanisms" not in forbid


def test_operations_plan_has_part_a2_changes():
    text = (Path(__file__).resolve().parents[1] / "docs" / "superpowers" / "plans" / "2026-10-25-revision-operations.md").read_text()
    assert "## Changes in Part A2" in text and "decision_h4" in text and "defender_commit" in text
    part_b = text.split("## Part B", 1)[1]
    assert part_b.index("### Operation 3") < part_b.index("### Operation 1")              # H4 after the defenders are frozen
    assert "R3-t | R4-t" not in part_b and "| fixtures" not in part_b and "--kind fixtures" not in part_b
