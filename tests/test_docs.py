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


def test_amendment_2_note_records_the_orchestration_and_the_runbook_carries_the_complete_commands():
    import hashlib
    note = (ROOT / "docs" / "amendments" / "2026-10-17-amendment-2.md").read_text()
    for s in ("lock-2026-10-17-amendment-2", "not expressible", "k_t = 5", "orchestration", "f5_bank", "--bank-from", "stress test", "Expected delta"):
        assert s in note, s
    for rel in ("experiments/tuned/tuned_B1.json", "experiments/tuned/tuned_B2.json", "experiments/tuned/tuned_B3.json", "experiments/calibration.json",
                "experiments/calibration_T100.json", "experiments/coverage_report.json", "experiments/coverage_report_amendment.json", "experiments/coverage_cells.json",
                "experiments/pilot_anthropic.json", "experiments/pilot_jev.json", "experiments/amendment-2026-10-17.yaml"):
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() in note, rel            # every registered artifact's hash, as the note records it
    assert "held out" not in note.lower().replace("never called held out", "").replace("never held out", "")
    for f in ("sol-rule-plan-r5.md", "astra-rule-plan-r5.md", "brief-rule-plan-review-r5.md"):
        assert (ROOT / "docs" / "amendments" / "roster" / f).exists(), f
    rb = (ROOT / "docs" / "lock-runbook.md").read_text()
    for s in ("scripts/tune_proposed.py --calibration experiments/calibration.json --sweep-out results/sweep --tuned-dir experiments/tuned --out experiments/proposed.yaml --log results/tuning_proposed",
              "scripts/describe_proposed.py --params experiments/proposed.yaml --out experiments/proposed_describe.yaml",
              "--sections development,rho_sweep,h3,all_deviators,ablation --rules B1,B2,B3,proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned",
              "scripts/falsify_proposed.py --calibration experiments/calibration.json --tuned-dir experiments/tuned --sweep-out results/sweep_proposed --out results/falsification",
              "--verify-lock lock-2026-10-17-amendment-2 --proposed proposed", "--bank-from results/sweep_proposed", "--proposed none",
              "scripts/amend.py --amendment experiments/amendment-2026-10-17.yaml --report experiments/coverage_report_amendment.json --base-report experiments/coverage_report.json --selection experiments/coverage_cells.json --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --check"):
        assert s in rb, s
