import re
from pathlib import Path

from sim.sealed import BUNDLE_FILES

ROOT = Path(__file__).resolve().parents[1]


def test_custodian_bundle_paths_match_the_loader_and_runbook_scripts_exist():
    text = (ROOT / "docs" / "custodian.md").read_text()
    paths = set(re.findall(r"`sealed/([A-Za-z0-9_./-]+)`", text))
    from sim.sealed import ACCESS_LOG
    assert {p for p in paths if not p.startswith("patches/") and not p.endswith("/") and p != ACCESS_LOG} == set(BUNDLE_FILES)   # the access log is named too and is outside the hash
    rb = (ROOT / "docs" / "lock-runbook.md").read_text()
    for script in set(re.findall(r"scripts/([a-z_]+\.py)", rb)):
        assert (ROOT / "scripts" / script).exists(), script


def test_amendment_file_is_binding_and_its_paths_exist():
    import yaml
    from pathlib import Path
    from sim.amendment import LIMITATION, load_amendment
    from sim.locked import load_locked
    ROOT = Path(__file__).resolve().parents[1]
    lk = load_locked(); am = load_amendment(ROOT / "experiments" / "amendment-2026-10-17.yaml", lk)
    assert am["clause"]["gain_reduction_min"] == 0.10 and am["clause"]["n"] == 40 and am["clause"]["requires_h2_rule_clause"] is True
    assert am["seeds_ext"] == {"start": 6_600_000, "block": 400_000, "pool": 35_000, "replications": {"40": 4000}}
    assert set(am["design"]) >= {"allocation", "audit_count", "audit_selection", "enforce", "tol", "L", "memory"} and am["tuning"]["grid_size"] == 36
    assert len(am["falsification"]["tests"]) == 5 and am["falsification"]["gate"]
    assert am["extension"]["limitation"] == LIMITATION and "held out" not in yaml.safe_dump(am).lower() and "held-out" not in yaml.safe_dump(am).lower()
    assert am["coverage_report_amendment_sha256"] is None or len(am["coverage_report_amendment_sha256"]) == 64
    assert (ROOT / "docs" / "amendments" / "2026-10-17-amendment-1.md").exists() and (ROOT / "docs" / "amendments" / "roster" / "consensus-final.md").exists()
    rb = (ROOT / "docs" / "lock-runbook.md").read_text()
    for s in ("scripts/coverage_ext.py", "scripts/amend.py", "--check", "lock-2026-10-17-amendment-1", "--coverage-ext", "--proposed none", "stress test"):
        assert s in rb, s
