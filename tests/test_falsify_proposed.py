"""The falsification helpers of the proposed rule (amendment 2, task A4), on synthetic histories and rows, plus the
harness's refusal of a sweep directory without the proposed rule's records."""
import json
import math
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import yaml
from scipy.stats import norm

from sim.mechanisms.base import AuditRecord, Consequences, RoundRecord

ROOT = Path(__file__).resolve().parents[1]
SYNTH = (ROOT / "tests" / "test_tune_proposed_script.py").read_text().split("SYNTH = '''")[1].split("'''")[0]


def fake_result(rounds, generation):
    """rounds: per round (assignment job->identity, audited [(job, identity, failed)], bans {identity: rounds})."""
    hist = []
    for t, (assignment, audited, bans) in enumerate(rounds):
        recs = tuple(AuditRecord(job=j, provider=i, delivered=0.0, claim=1.0, failed=bool(f)) for j, i, f in audited)
        hist.append(RoundRecord(t=t, offers={}, assignment=dict(assignment), payments={}, audits=recs, consequences=Consequences(bans=dict(bans))))
    return types.SimpleNamespace(history=tuple(hist), identity_generation=tuple(generation), audits=np.array([len(r.audits) for r in hist]))


def test_f2_rows_cover_the_sole_entrant_only_when_the_round_allowance_permits():
    from scripts.falsify_proposed import f2_corner_rounds
    six = {j: 3 for j in range(6)}; others = {j: 0 for j in range(6, 12)}
    rounds = [
        ({**six, **others}, [(j, 3, False) for j in range(6)] + [(j, 0, False) for j in range(6, 10)], {}),        # k = 10 >= 6, all six audited: pass
        ({**six, **others}, [(j, 3, False) for j in range(5)] + [(j, 0, False) for j in range(6, 11)], {}),        # k = 10 >= 6, five audited: fail
        ({**six, **others}, [(j, 3, False) for j in range(4)], {}),                                                 # k = 4 < 6: not applicable
        ({**six, 6: 4, 7: 0}, [(0, 3, False)], {}),                                                                 # two replacement identities: no row
        (others, [(6, 0, False)], {}),                                                                              # no replacement identity: no row
    ]
    res = fake_result(rounds, generation=(0, 0, 0, 1, 1))
    rows = f2_corner_rounds(res, None)
    assert [r["round"] for r in rows] == [0, 1, 2]
    assert rows[0] == {"round": 0, "identity": 3, "served": 6, "k": 10, "audited": 6, "applicable": True, "pass": True}
    assert rows[1]["audited"] == 5 and rows[1]["applicable"] and rows[1]["pass"] is False
    assert rows[2] == {"round": 2, "identity": 3, "served": 6, "k": 4, "audited": 4, "applicable": False, "pass": None}
    assert f2_corner_rounds(res, [10, 10, 4, 1, 1]) == rows


def test_f3_expectations_follow_the_audited_exposure_and_clip_bans_at_the_episode_end():
    from scripts.falsify_proposed import f3_expected_failures_and_bans
    tol, sigma = 0.12, 0.1; p = float(norm.cdf(-tol / sigma))
    rounds = [
        ({0: 0, 1: 0, 2: 1}, [(0, 0, True), (1, 0, False), (2, 1, False)], {0: 10}),      # identity 0: a = 2, one failure, banned 10 (clipped to 4 rounds)
        ({3: 1, 4: 1, 5: 1}, [(3, 1, False), (4, 1, False), (5, 1, False)], {}),         # identity 1: a = 3
        ({}, [], {}), ({}, [], {}), ({}, [], {}),
    ]
    res = fake_result(rounds, generation=(0, 0))
    d = f3_expected_failures_and_bans(res, tol, sigma, L=10)
    assert d["p"] == pytest.approx(p) and d["audited"] == 6 and d["observed_failures"] == 1 and d["expected_failures"] == pytest.approx(6 * p)
    assert d["observed_ban_events"] == 1
    assert d["expected_ban_events"] == pytest.approx((1 - (1 - p) ** 2) + (1 - (1 - p)) + (1 - (1 - p) ** 3))
    assert d["observed_lost_rounds"] == 4
    assert d["expected_lost_rounds"] == pytest.approx((1 - (1 - p) ** 2) * 4 + (1 - (1 - p)) * 4 + (1 - (1 - p) ** 3) * 3)


def rows(seeds, gains, effs):
    return [{"seed": int(s), "gain": float(g), "eff_attack": float(e)} for s, g, e in zip(seeds, gains, effs)]


def test_f4_cell_gate_kills_on_thresholds_and_compares_b3_by_the_paired_standard_error():
    from scripts.falsify_proposed import f4_cell_gate
    rng = np.random.default_rng(0); seeds = range(2000, 2020)
    prop = rows(seeds, 0.10 + 0.01 * rng.standard_normal(20), 0.95 + 0.005 * rng.standard_normal(20))
    b3 = rows(seeds, 0.20 + 0.01 * rng.standard_normal(20), 0.93 + 0.005 * rng.standard_normal(20))
    d = f4_cell_gate(prop, b3)
    assert d["n"] == 20 and not d["kill"] and not d["comparative_fails"] and d["mean_gain"] == pytest.approx(np.mean([r["gain"] for r in prop]))
    assert d["diff_gain_se"] > 0 and d["diff_gain_mean"] == pytest.approx(np.mean([a["gain"] - b["gain"] for a, b in zip(b3, prop)]))
    assert f4_cell_gate(rows(seeds, [0.35] * 20, [0.95] * 20), b3)["kill"]
    assert f4_cell_gate(prop, rows(seeds, [0.89] * 20, [0.95] * 20))["kill"] is False and f4_cell_gate(rows(seeds, [0.1] * 20, [0.89] * 20), b3)["kill"]
    better = rows(seeds, 0.00 + 0.001 * rng.standard_normal(20), 0.95 + 0.005 * rng.standard_normal(20))       # B3's gain lower beyond two standard errors
    assert f4_cell_gate(prop, better)["comparative_fails"]
    with pytest.raises(ValueError, match="seed"):
        f4_cell_gate(prop, rows(range(2001, 2021), [0.2] * 20, [0.93] * 20))


def test_f5_gain_reduction_bounds_and_the_doubling_record():
    from scripts.falsify_proposed import f5_gain_reduction
    rng = np.random.default_rng(1); seeds = range(2000, 2020); settings = {"bootstrap_resamples": 400, "bootstrap_seed": 7}
    h3 = {"proposed": rows(seeds, 0.05 + 0.02 * rng.standard_normal(20), [0.95] * 20),
          "B2": rows(seeds, 0.58 + 0.03 * rng.standard_normal(20), [0.9] * 20), "B3": rows(seeds, 0.36 + 0.03 * rng.standard_normal(20), [0.9] * 20)}
    d = f5_gain_reduction(h3, {"doubling": {"delta_gain": 0.001}}, settings)
    assert set(d["reductions"]) == {"B2", "B3"} and all(v["lower_bound"] >= 0.10 and v["level"] == 0.9875 and v["method"] == "studentized" for v in d["reductions"].values())
    assert d["doubling_pass"] and d["delta_gain"] == 0.001 and d["pass"] and not d["kill"]
    bad = f5_gain_reduction(h3, {"doubling": {"delta_gain": 0.02}}, settings)
    assert not bad["doubling_pass"] and bad["kill"]
    weak = dict(h3, B3=rows(seeds, 0.12 + 0.03 * rng.standard_normal(20), [0.9] * 20))
    assert f5_gain_reduction(weak, {"doubling": {"delta_gain": 0.0}}, settings)["kill"]
    with pytest.raises(ValueError, match="doubling"):
        f5_gain_reduction(h3, None, settings)


@pytest.mark.slow
def test_harness_refuses_a_sweep_directory_without_the_proposed_rules_records(tmp_path, cal_path_session, monkeypatch):
    mod = tmp_path / "proposed.py"; mod.write_text(SYNTH)
    params = tmp_path / "proposed.yaml"
    params.write_text(yaml.safe_dump({"rule": "proposed", "quick": True, "best_params": {"allocation": "A", "targeting": "T1", "tol": 0.12, "L": 10}}))
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_MODULE", str(mod)); monkeypatch.setenv("TOUCHSTONE_PROPOSED_PARAMS", str(params))
    sweep = tmp_path / "sweep"; (sweep / "evaluate").mkdir(parents=True)
    cmd = [sys.executable, str(ROOT / "scripts" / "falsify_proposed.py"), "--calibration", str(cal_path_session), "--tuned-dir", str(ROOT / "experiments" / "tuned"),
           "--sweep-out", str(sweep), "--out", str(tmp_path / "fals"), "--params", str(params), "--quick"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env={**__import__("os").environ, "OMP_NUM_THREADS": "1"})
    assert r.returncode != 0 and "proposed_D2_beta0.05_rho0.2_median_development" in (r.stderr + r.stdout)
    assert not (tmp_path / "fals" / "report.json").exists()
