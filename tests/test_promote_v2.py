"""Staged promotion (operations plan Task 5). Outputs come from the producers themselves at production arguments, with the
expensive calls stubbed (the per-(configuration, market) scorer, the pool builder, the endpoint miss counts, the benchmark
workloads), so budgets, counts, and metadata are the registered ones. Each refusal mutates one field of a valid output."""
import json
import shutil
import time
from pathlib import Path

import pytest

MARKETS = ["headline", "dev0", "dev1"]
SYSTEMS = ("B3-t", "R3-t", "C*-t")


def _score(rule, spec, label, budget, recheck):
    v = -abs(spec["tol"] - 0.12) - abs(spec["L"] - 10) / 100 + (0.001 if (spec.get("cred") or {}).get("variant") == "mem" else 0.0)
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


@pytest.fixture(scope="module")
def produced(tmp_path_factory):
    """Every producer's output once, and a destination with the tuning kinds already promoted (coverage reads them)."""
    import scripts.benchmark_v2 as BV
    import scripts.coverage_v2 as CV
    import scripts.promote_v2 as P
    import scripts.tune_v2 as TV
    import sim.calibration_v2 as C
    root = tmp_path_factory.mktemp("produced")
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(TV, "_score_market", _score)
        TV.select_comparator(MARKETS, root / "cmp")
        cred = json.loads((root / "cmp" / "comparator.json").read_text())["cred"]
        for s in SYSTEMS:
            TV.tune_system(s, MARKETS, root / "sys" / s, cred=cred if s == "C*-t" else None)
        TV.select_comparator(MARKETS, root / "cmp_smoke", smoke=True)
        to = root / "v2"; head = P.head()
        P.promote("comparator", root / "cmp", to, MARKETS, code_commit=head)
        for s in SYSTEMS:
            P.promote("system", root / "sys" / s, to, MARKETS, code_commit=head)
        mp.setattr(C, "build_pool", _fake_pool); mp.setattr(C, "endpoint_misses", _misses)
        for m in MARKETS:
            CV.main(["--pools", "--market", m, "--inputs", str(to), "--out", str(root / "cov")])
        CV.main(["--select", "--out", str(root / "cov")]); CV.main(["--validate", "--out", str(root / "cov")])
        stub = {k: (lambda: time.sleep(0.002)) for k in BV.WORKLOADS}
        mp.setattr(BV, "_default_fns", lambda out, smoke=False: stub)
        BV.main(["--run", "--usd-per-pod-hour", "0.56", "--workers", "16", "--out", str(root / "bench")])
        lg = root / "ledger.json"; lg.write_text(json.dumps({"caps": {"development": 12.0, "evaluation": 40.0}, "reservations": [], "spent": []}))
        BV.main(["--decide", str(root / "bench" / "timings.json"), "--ledger", str(lg), "--out", str(root / "dec" / "decision.json")])
    return {"root": root, "to": to, "head": head, "cred": cred}


def _clone_dest(produced, tmp_path):
    d = tmp_path / "v2"; shutil.copytree(produced["to"], d)
    return d


def test_unedited_producer_outputs_pass_schema(produced, tmp_path):
    import scripts.promote_v2 as P
    r, h = produced["root"], produced["head"]; to = _clone_dest(produced, tmp_path)
    P.promote("coverage", r / "cov", to, MARKETS, branch="three20k", code_commit=h)
    P.promote("benchmark", r / "bench", to, ["headline", "dev0"], code_commit=h)
    P.promote("decision", r / "dec", to, MARKETS, code_commit=h)
    prom = json.loads((to / "promotion.json").read_text())
    assert {"comparator.json", "coverage.json", "benchmark/timings.json", "benchmark/decision.json"} <= set(prom["entries"])
    assert "fixture_cstar_s2.json" not in prom["entries"]
    assert all(f"tuned_{s}.json" in prom["entries"] for s in SYSTEMS) and any(p.startswith("pools/") for p in prom["entries"])


def test_smoke_outputs_are_refused(produced, tmp_path):
    import scripts.promote_v2 as P
    with pytest.raises(P.Refused, match="smoke"):
        P.promote("comparator", produced["root"] / "cmp_smoke", tmp_path / "v2", MARKETS, code_commit=produced["head"])


def _edit(path: Path, fn):
    d = json.loads(path.read_text()); fn(d); path.write_text(json.dumps(d))


def _top_cred_changed(d):
    d["cred"] = dict(d["cred"], K=d["cred"]["K"] + 1)


def _first_endpoint(d, key, val):
    d["Q4"]["validation"]["endpoints"][0][key] = val


MUTATIONS = {
    "comparator smoke": ("comparator", "cmp", "comparator.json", lambda d: d.update(smoke=True), "smoke"),
    "comparator commit": ("comparator", "cmp", "comparator.json", lambda d: d.update(commit="0" * 40), "commit"),
    "comparator markets": ("comparator", "cmp", "comparator.json", lambda d: d.update(markets=["headline", "dev0"]), "markets"),
    "comparator 11 scored": ("comparator", "cmp", "comparator.json", lambda d: d["scores"].pop(), "12"),
    "comparator 1 recheck": ("comparator", "cmp", "comparator.json", lambda d: d["rechecked"].pop(), "recheck"),
    "comparator inner budget": ("comparator", "cmp", "comparator.json", lambda d: d.update(budget_inner=[1, 16, 1, 2]), "budget"),
    "comparator cred not the top recheck": ("comparator", "cmp", "comparator.json", _top_cred_changed, "cred"),
    "system 15 scored": ("system", "sys/B3-t", "tuned_B3-t.json", lambda d: d["scores"].pop(), "16"),
    "system best not the top recheck": ("system", "sys/R3-t", "tuned_R3-t.json", lambda d: d.update(best_params={"tol": 0.08, "L": 50}), "best"),
    "system full budget": ("system", "sys/R3-t", "tuned_R3-t.json", lambda d: d.update(budget_full=[1, 16, 1, 2]), "budget"),
    "coverage substituted endpoint": ("coverage", "cov", "coverage.json", lambda d: _first_endpoint(d, "alpha_e", 0.5), "endpoint"),
    "coverage admitted with a failing endpoint": ("coverage", "cov", "coverage.json", lambda d: _first_endpoint(d, "misses", 19_000), "admi"),
    "coverage kappa_effective changed to 1": ("coverage", "cov", "coverage.json", lambda d: d["Q1"].update(kappa_effective=1.0), "kappa"),
    "coverage validation replications": ("coverage", "cov", "coverage.json", lambda d: d["Q4"].update(validation_replications=19_999), "replications"),
    "coverage resamples": ("coverage", "cov", "coverage.json", lambda d: d["Q1"].update(resamples=999), "resamples"),
    "coverage smoke": ("coverage", "cov", "coverage.json", lambda d: d.update(smoke=True), "smoke"),
    "coverage pool size": ("coverage", "cov", "coverage.json", lambda d: d.update(pool_size=40), "pool"),
    "coverage inputs from another tuning set": ("coverage", "cov", "coverage.json", lambda d: d["inputs_manifest"].update({"comparator.json": "f" * 64}), "inputs"),
    "coverage pool hash": ("coverage", "cov", "coverage.json", lambda d: d["pools"]["dev0"].update(sha256="0" * 64), "pool"),
    "benchmark smoke": ("benchmark", "bench", "timings.json", lambda d: d["timings"].update(smoke=True), "smoke"),
    "benchmark markets": ("benchmark", "bench", "timings.json", lambda d: d["timings"].update(markets=["headline"]), "markets"),
    "benchmark table": ("benchmark", "bench", "cost_table.json", lambda d: d.update(total_usd=d["total_usd"] + 1.0), "table"),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_each_refusal(produced, tmp_path, name):
    import scripts.promote_v2 as P
    kind, sub, fname, fn, needle = MUTATIONS[name]
    src = tmp_path / "src"; shutil.copytree(produced["root"] / sub, src); _edit(src / fname, fn)
    to = _clone_dest(produced, tmp_path) if kind in ("coverage", "benchmark", "system") else tmp_path / "v2"
    if kind == "system" and not (to / "comparator.json").exists():
        P.promote("comparator", produced["root"] / "cmp", to, MARKETS, code_commit=produced["head"])
    kw = {"branch": "three20k"} if kind == "coverage" else {}
    markets = ["headline", "dev0"] if kind == "benchmark" else MARKETS
    with pytest.raises(P.Refused, match=needle):
        P.promote(kind, src, to, markets, code_commit=produced["head"], **kw)


def test_coverage_wrong_branch_and_short_pools_are_refused(produced, tmp_path):
    import scripts.promote_v2 as P
    to = _clone_dest(produced, tmp_path)
    with pytest.raises(P.Refused, match="branch"):
        P.promote("coverage", produced["root"] / "cov", to, MARKETS, branch="two20k", code_commit=produced["head"])
    src = tmp_path / "short"; shutil.copytree(produced["root"] / "cov", src)
    _edit(src / "pools" / "dev0.json", lambda d: (d.update(seeds=d["seeds"][:40]), [v.__delitem__(slice(40, None)) for v in d["normalized"].values()]))
    with pytest.raises(P.Refused, match="pool"):
        P.promote("coverage", src, to, MARKETS, branch="three20k", code_commit=produced["head"])


def test_staged_kinds_promote_independently(produced, tmp_path):
    import scripts.promote_v2 as P
    to = tmp_path / "v2"
    P.promote("comparator", produced["root"] / "cmp", to, MARKETS, code_commit=produced["head"])
    entries = json.loads((to / "promotion.json").read_text())["entries"]
    assert "comparator.json" in entries and not any(p.startswith("tuned_") for p in entries)
    with pytest.raises(P.Refused, match="comparator"):
        P.promote("system", produced["root"] / "sys" / "C*-t", tmp_path / "other", MARKETS, code_commit=produced["head"])


def test_final_needs_all_kinds_and_writes_params(produced, tmp_path):
    import scripts.promote_v2 as P
    r, h = produced["root"], produced["head"]; to = _clone_dest(produced, tmp_path)
    with pytest.raises(P.Refused, match="missing"):
        P.final(to)
    P.promote("coverage", r / "cov", to, MARKETS, branch="three20k", code_commit=h)
    P.promote("benchmark", r / "bench", to, ["headline", "dev0"], code_commit=h)
    P.promote("decision", r / "dec", to, MARKETS, code_commit=h)
    params = P.final(to)
    tuned = {s: json.loads((r / "sys" / s / f"tuned_{s}.json").read_text())["best_params"] for s in SYSTEMS}
    assert params == {"cred": produced["cred"], "tuned": tuned} and json.loads((to / "params.json").read_text()) == params



# ---- final review K5: promoted bytes are checked at --final -------------------------------------------------------------------

def test_k5_final_refuses_a_file_changed_after_promotion(produced, tmp_path):
    import scripts.promote_v2 as P
    r, h = produced["root"], produced["head"]; to = _clone_dest(produced, tmp_path)
    P.promote("coverage", r / "cov", to, MARKETS, branch="three20k", code_commit=h)
    P.promote("benchmark", r / "bench", to, ["headline", "dev0"], code_commit=h)
    P.promote("decision", r / "dec", to, MARKETS, code_commit=h)
    _edit(to / "tuned_B3-t.json", lambda d: d.update(best_params={"tol": 0.08, "L": 50}))
    with pytest.raises(P.Refused, match="hash"):
        P.final(to)
    assert P.verify_promoted(to) and not (to / "params.json").exists()



def test_k4_promotion_refuses_a_pool_from_another_commit(produced, tmp_path):
    import hashlib
    import scripts.promote_v2 as P
    src = tmp_path / "src"; shutil.copytree(produced["root"] / "cov", src)
    pool = src / "pools" / "dev1.json"; _edit(pool, lambda d: d.update(commit="f" * 40))
    _edit(src / "coverage.json", lambda d: d["pools"]["dev1"].update(sha256=hashlib.sha256(pool.read_bytes()).hexdigest()))
    with pytest.raises(P.Refused, match="commit"):
        P.promote("coverage", src, _clone_dest(produced, tmp_path), MARKETS, branch="three20k", code_commit=produced["head"])


def test_promote_systems_three_and_no_fixture_kind():
    import scripts.promote_v2 as P
    assert P.SYSTEMS == ("B3-t", "R3-t", "C*-t") and "fixtures" not in P.CHECKS


def test_final_promotion_three_systems(produced, tmp_path):
    import scripts.promote_v2 as P
    r, h = produced["root"], produced["head"]; to = _clone_dest(produced, tmp_path)
    P.promote("coverage", r / "cov", to, MARKETS, branch="three20k", code_commit=h)
    P.promote("benchmark", r / "bench", to, ["headline", "dev0"], code_commit=h)
    P.promote("decision", r / "dec", to, MARKETS, code_commit=h)
    assert not (to / "fixture_cstar_s2.json").exists() and set(P.final(to)["tuned"]) == set(SYSTEMS)

