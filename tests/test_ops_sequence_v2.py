"""The revised operations sequence of design draft 7 (Part A2 Task 12), executable in a temporary git repository: the code
commit, comparator and system promotions, the data-only defender-freeze commit, the H4 check's actual export record, the
decision after the H4 timing with its independent identifiers, coverage produced across a later documentation-only commit
with the registered arguments (the expensive computation replaced by test substitutes), the final promotion, and the lock.
Refused variants: smoke coverage, pools from changed code, a wrong bundle hash or defender commit, a tuned file changed
after the defender freeze, and a protocol whose H4 hash differs from the author's commitment."""
import json
import shutil
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MARKETS = ["headline", "dev0", "dev1"]
TOY = ROOT / "tests" / "fixtures" / "h4_toy"


def git(repo, *args) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(repo, msg) -> str:
    git(repo, "add", "-A"); git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", msg)
    return git(repo, "rev-parse", "HEAD")


def _score(rule, spec, label, budget, recheck):
    v = -abs(spec["tol"] - 0.12) - abs(spec["L"] - 10) / 100
    att = {"u0": 0.2, "m0": 0.1}
    return {"label": label, "margins": {"D2": v, "D2+H3": v + 0.01, "X7-SC": v + 0.02},
            "detail": {"D2": {"eff": 0.97, "gain": 0.1, "attack": att}, "D2+H3": {"eff": 0.96, "gain": 0.1, "attack": att},
                       "X7-SC": {"eff": 0.95, "gain": 0.1, "attack": att}, "reference": {"name": "honest_max", "family": None, "T": 200, "L": 10, "knobs": None}},
            "episodes": 3}


def _fake_pool(mkt, attacks, refs, seeds, cred):
    from sim.calibration_v2 import PROFILES
    k = lambda p: "|".join(p)
    return {"seeds": list(seeds), "normalized": {k(p): [0.0] * len(seeds) for p in PROFILES}, "eff": {k(p): [0.95] * len(seeds) for p in PROFILES}}


def _misses(family, fixtures, branch, kappa, replications, seed, resamples):
    from sim.calibration_v2 import endpoints
    return {i: (0 if kappa <= 0.25 else replications) for i, _ in enumerate(endpoints(family, branch))}


@pytest.fixture()
def world(tmp_path, monkeypatch):
    import scripts.benchmark_v2 as BV
    import scripts.h4_check as HC
    import scripts.promote_v2 as P
    import scripts.revision_v2 as RV
    import scripts.tune_v2 as TV
    import sim.calibration_v2 as C
    repo = tmp_path / "repo"; (repo / "sim").mkdir(parents=True); (repo / "experiments" / "v2").mkdir(parents=True); (repo / "docs" / "revision").mkdir(parents=True)
    git(repo, "init", "-q"); git(repo, "config", "user.email", "t@t"); git(repo, "config", "user.name", "t")
    (repo / "sim" / "code.py").write_text("x = 1\n")
    shutil.copy(ROOT / "experiments" / "revision-v2-manifest.yaml", repo / "experiments" / "revision-v2-manifest.yaml")
    code = commit(repo, "code")
    head = {"c": code}
    monkeypatch.setattr(RV, "git_commit", lambda: head["c"])
    monkeypatch.setattr(TV, "_score_market", _score); monkeypatch.setattr(C, "build_pool", _fake_pool); monkeypatch.setattr(C, "endpoint_misses", _misses)
    import scripts.coverage_v2 as CV
    monkeypatch.setattr(CV, "REPO", repo)
    to = repo / "experiments" / "v2"; work = tmp_path / "work"
    TV.select_comparator(MARKETS, work / "cmp")
    cred = json.loads((work / "cmp" / "comparator.json").read_text())["cred"]
    for s in TV.SYSTEMS:
        TV.tune_system(s, MARKETS, work / "sys" / s, cred=cred if s == "C*-t" else None)
    P.promote("comparator", work / "cmp", to, MARKETS, code_commit=code, repo=repo)
    for s in TV.SYSTEMS:
        P.promote("system", work / "sys" / s, to, MARKETS, code_commit=code, repo=repo)
    stub = {k: (lambda: time.sleep(0.001)) for k in BV.WORKLOADS}
    monkeypatch.setattr(BV, "_default_fns", lambda out, smoke=False: stub)
    BV.main(["--run", "--usd-per-pod-hour", "0.56", "--workers", "16", "--out", str(work / "bench")])
    led = repo / "docs" / "revision" / "budget-ledger.json"
    led.write_text(json.dumps({"caps": {"development": 12.0, "evaluation": 40.0}, "reservations": [], "spent": [{"op": "development", "tag": "bench", "usd": 1.0}], "approval": None}))
    BV.main(["--decide", str(work / "bench" / "timings.json"), "--ledger", str(led), "--out", str(work / "dec" / "decision.json")])
    P.promote("benchmark", work / "bench", to, ["headline", "dev0"], code_commit=code, repo=repo)
    P.promote("decision", work / "dec", to, MARKETS, code_commit=code, repo=repo)
    defender = commit(repo, "defender freeze (data only)"); head["c"] = defender
    # the sealed session: the actual check, with the full-budget timed searches replaced by fixed measurements
    bundle = tmp_path / "sealed2"; shutil.copytree(TOY, bundle)
    full = 5 * 600 * 2 * 5
    monkeypatch.setattr(HC, "smoke", lambda *a, **k: {"stub": True})
    monkeypatch.setattr(HC, "_timed_search", lambda j, fam, budget: (40.0 if fam.name == "H4" else 20.0, full, 300))
    (tmp_path / "cmp.json").write_text(json.dumps({"cred": cred}))
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert HC.main(["--bundle", str(bundle), "--comparator", str(tmp_path / "cmp.json"), "--defender-commit", defender]) == 0
    export = buf.getvalue().strip().splitlines()[-1]
    h4dir = to / "h4"; h4dir.mkdir()
    (h4dir / "timing.json").write_text(export + "\n")
    rec = json.loads(export)
    (h4dir / "commitment.json").write_text(json.dumps({"bundle_sha256": rec["bundle_sha256"], "defender_commit": defender}))
    return {"repo": repo, "to": to, "work": work, "code": code, "defender": defender, "head": head, "led": led, "export": rec, "cred": cred}


def _decide_and_promote_h4(w):
    import scripts.benchmark_v2 as BV
    import scripts.promote_v2 as P
    to = w["to"]; h4dir = to / "h4"
    out = h4dir / "decision-h4.json"
    if out.exists():
        out.unlink()
    assert BV.main(["--decide-h4", str(h4dir / "timing.json"), "--timings", str(to / "benchmark" / "timings.json"), "--frozen", str(to / "benchmark" / "decision.json"),
                    "--ledger", str(w["led"]), "--out", str(out)]) == 0
    return P.promote("decision_h4", h4dir, to, MARKETS, code_commit=w["code"], repo=w["repo"])


def _coverage(w, monkeypatch, head):
    import scripts.coverage_v2 as CV
    w["head"]["c"] = head
    cov = w["work"] / f"cov-{head[:7]}"
    for m in MARKETS:
        assert CV.main(["--pools", "--market", m, "--inputs", str(w["to"]), "--code-commit", w["code"], "--out", str(cov)]) == 0
    assert CV.main(["--select", "--code-commit", w["code"], "--out", str(cov)]) == 0
    assert CV.main(["--validate", "--code-commit", w["code"], "--out", str(cov)]) == 0
    return cov


def test_ops_sequence_draft7(world, monkeypatch):
    import scripts.benchmark_v2 as BV
    import scripts.promote_v2 as P
    from scripts.lock_v2 import build
    w = world
    _decide_and_promote_h4(w)
    dh4 = json.loads((w["to"] / "benchmark" / "decision-h4.json").read_text())
    assert dh4["decision"]["h4_ratio"] == pytest.approx(2.0) and dh4["h4_timing"] == w["export"]
    doc = commit_docs(w["repo"])
    cov = _coverage(w, monkeypatch, doc)
    P.promote("coverage", cov, w["to"], MARKETS, branch="three20k", code_commit=w["code"], repo=w["repo"])
    params = P.final(w["to"], h4=True)
    assert set(params["tuned"]) == {"B3-t", "R3-t", "C*-t"}
    (w["repo"] / "docs" / "revision" / "predictions-v2.md").write_text("# Predictions\n")
    dec = dh4["decision"]; h4 = {"commit": "f" * 40, "bundle_sha256": w["export"]["bundle_sha256"]}
    p = build(w["repo"], w["code"], dec["cuts"], h4, None, dec["branch"], dec["markets"])
    assert p["decision_sha256"] == P._sha(w["to"] / "benchmark" / "decision-h4.json")
    t = json.loads((w["to"] / "benchmark" / "timings.json").read_text())["timings"]
    pod = BV.cost_table(t, vcpu=16, h4_timing=w["export"])["evaluation_usd"]; units = BV.cost_table(t, 0.108, h4_timing=w["export"])["evaluation_units"]
    assert pod > BV.cost_table(t, vcpu=16)["evaluation_usd"] and units > BV.cost_table(t, 0.108)["evaluation_units"]   # both billing paths price H4 from it
    with pytest.raises(SystemExit):
        build(w["repo"], w["code"], dec["cuts"], {"commit": "f" * 40, "bundle_sha256": "0" * 64}, None, dec["branch"], dec["markets"])


def commit_docs(repo) -> str:
    (repo / "docs" / "note.md").write_text("ops ledger\n")
    return commit(repo, "docs only")


def test_refused_identifiers_and_changed_defenders(world):
    import scripts.promote_v2 as P
    w = world; h4dir = w["to"] / "h4"
    good = (h4dir / "commitment.json").read_text()
    (h4dir / "commitment.json").write_text(json.dumps({**json.loads(good), "bundle_sha256": "0" * 64}))
    with pytest.raises(P.Refused, match="bundle"):
        _decide_and_promote_h4(w)
    (h4dir / "commitment.json").write_text(json.dumps({**json.loads(good), "defender_commit": w["code"]}))
    with pytest.raises(P.Refused, match="defender"):
        _decide_and_promote_h4(w)
    (h4dir / "commitment.json").write_text(good)
    t = w["to"] / "tuned_B3-t.json"; d = json.loads(t.read_text()); d["best_params"] = {"tol": 0.08, "L": 50}; t.write_text(json.dumps(d))
    with pytest.raises(P.Refused, match="defender"):
        _decide_and_promote_h4(w)


def test_refused_pools_from_changed_code_and_smoke(world, monkeypatch):
    import scripts.coverage_v2 as CV
    import scripts.promote_v2 as P
    w = world
    _decide_and_promote_h4(w)
    (w["repo"] / "sim" / "code.py").write_text("x = 2\n")
    changed = commit(w["repo"], "code change")
    w["head"]["c"] = changed
    cov = w["work"] / "cov-changed"
    with pytest.raises(SystemExit):
        for m in MARKETS:
            CV.main(["--pools", "--market", m, "--inputs", str(w["to"]), "--code-commit", w["code"], "--out", str(cov)])
        CV.main(["--select", "--code-commit", w["code"], "--out", str(cov)])
    smoke = w["work"] / "cov-smoke"; w["head"]["c"] = w["defender"]
    for m in MARKETS:
        CV.main(["--pools", "--market", m, "--inputs", str(w["to"]), "--code-commit", w["code"], "--pool-size", "40", "--out", str(smoke)])
    CV.main(["--select", "--code-commit", w["code"], "--replications", "10", "--out", str(smoke)])
    CV.main(["--validate", "--code-commit", w["code"], "--replications", "10", "--out", str(smoke)])
    with pytest.raises(P.Refused, match="smoke"):
        P.promote("coverage", smoke, w["to"], MARKETS, branch="three20k", code_commit=w["code"], repo=w["repo"])
