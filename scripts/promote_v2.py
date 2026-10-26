"""Staged promotion of pulled outputs into experiments/v2 (operations plan Task 5). Each kind is validated against its
producer's schema and the registered procedure, then copied, and every copied file's SHA-256 is appended to
experiments/v2/promotion.json; a path already promoted with another hash is refused. --final checks that every kind is
present and writes params.json, the --params file of scripts/revision_v2.py. Kinds: comparator, system (one tuned file),
fixtures, coverage (with its pools), benchmark, decision."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import benchmark_v2 as BV  # noqa: E402
from scripts import tune_v2 as TV  # noqa: E402
from scripts.revision_v2 import git_commit  # noqa: E402
from sim import calibration_v2 as CAL  # noqa: E402
from sim.instances import coverage_pool  # noqa: E402
from sim.intervals import clopper_pearson_upper  # noqa: E402

SYSTEMS = ("B3-t", "R3-t", "R4-t", "C*-t")
KAPPAS = (1.0, 0.5, 0.25)
REGISTERED = {"selection": 10_000, "validation": 20_000, "resamples": 9999}
BENCH_MARKETS = ["headline", "dev0"]


class Refused(Exception):
    pass


def head() -> str:
    return git_commit()


def _sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _json(path) -> dict:
    return json.loads(Path(path).read_text())


def _require(ok: bool, msg: str) -> None:
    if not ok:
        raise Refused(msg)


def _promotion(to: Path) -> dict:
    p = Path(to) / "promotion.json"
    return _json(p) if p.exists() else {"entries": {}, "kinds": {}}


def _record(to: Path, kind: str, files: list[tuple[Path, str]]) -> list[str]:
    to = Path(to); prom = _promotion(to)
    for src, rel in files:
        h = _sha(src)
        _require(prom["entries"].get(rel, h) == h, f"{rel} is already promoted with another hash")
    for src, rel in files:
        dst = to / rel; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
        prom["entries"][rel] = _sha(dst); prom["kinds"].setdefault(kind, []).append(rel)
    (to / "promotion.json").write_text(json.dumps(prom, indent=1, sort_keys=True))
    return [rel for _, rel in files]


def _common(d: dict, code_commit: str, markets: list[str] | None, what: str) -> None:
    _require(d.get("smoke") is False, f"{what}: smoke outputs are not promoted")
    _require(d.get("commit") == code_commit, f"{what}: commit {d.get('commit')!r} differs from the code commit {code_commit!r}")
    if markets is not None:
        _require(list(d.get("markets") or []) == list(markets), f"{what}: markets {d.get('markets')} are not {list(markets)}")


def _budgets(d: dict, what: str) -> None:
    inner, full = TV._budgets(False)
    _require(list(d.get("budget_inner") or []) == list(inner), f"{what}: inner budget {d.get('budget_inner')} is not {list(inner)}")
    _require(list(d.get("budget_full") or []) == list(full), f"{what}: full budget {d.get('budget_full')} is not {list(full)}")


def _ranked(d: dict, n: int, what: str) -> None:
    sc, rc = d.get("scores") or [], d.get("rechecked") or []
    _require(len(sc) == n and [s["grid"] for s in sc] == list(range(n)), f"{what}: {len(sc)} scored configurations, not {n} in grid order")
    _require(len(rc) == TV.TOP, f"{what}: {len(rc)} rechecked configurations, not {TV.TOP}")
    _require([s["spec"] for s in rc] == [s["spec"] for s in TV.rank(sc)[:TV.TOP]] or sorted(json.dumps(s["spec"], sort_keys=True) for s in rc)
             == sorted(json.dumps(s["spec"], sort_keys=True) for s in TV.rank(sc)[:TV.TOP]), f"{what}: the rechecked configurations are not the top {TV.TOP}")


def _logs(src: Path, rule: str, specs: list[dict], markets: list[str], what: str) -> list[tuple[Path, str]]:
    files = []
    for f in sorted((Path(src) / "log").glob("*.json")):
        d = _json(f)
        if d.get("rule") == rule:
            _require(set(d.get("detail", {})) == set(markets), f"{what}: log {f.name} lacks markets {sorted(set(markets) - set(d.get('detail', {})))}")
            files.append((f, f"log/{f.name}"))
    seen = {json.dumps(_json(f)["spec"], sort_keys=True) for f, _ in files}
    _require(all(json.dumps(s, sort_keys=True) in seen for s in specs), f"{what}: a scored configuration has no log")
    return files


def _comparator(src, to, markets, code_commit):
    d = _json(Path(src) / "comparator.json"); what = "comparator"
    _common(d, code_commit, markets, what); _budgets(d, what); _ranked(d, len(TV.comparator_grid()), what)
    _require(d["cred"] == TV.rank(d["rechecked"])[0]["spec"]["cred"], f"{what}: cred is not the top rechecked configuration's")
    return [(Path(src) / "comparator.json", "comparator.json"), *_logs(src, "C*", [s["spec"] for s in d["scores"]], markets, what)]


def _promoted_cred(to) -> dict:
    p = Path(to) / "comparator.json"
    _require(p.exists(), "cred: the comparator is not promoted yet")
    return _json(p)["cred"]


def _system(src, to, markets, code_commit):
    tuned = sorted(Path(src).glob("tuned_*.json"))
    _require(len(tuned) == 1, f"system: {len(tuned)} tuned files in {src}")
    d = _json(tuned[0]); name = d.get("rule"); what = f"system {name}"
    _require(name in SYSTEMS, f"system: unknown rule {name!r}")
    _common(d, code_commit, markets, what); _budgets(d, what); _ranked(d, len(TV.COMMON_GRID), what)
    top = TV.rank(d["rechecked"])[0]["spec"]
    _require(d["best_params"] == {"tol": top["tol"], "L": top["L"]}, f"{what}: best parameters {d['best_params']} are not the top recheck's")
    if name == "C*-t":
        _require(d.get("cred") == _promoted_cred(to), f"{what}: cred differs from the promoted comparator's")
    return [(tuned[0], tuned[0].name), *_logs(src, name, [s["spec"] for s in d["scores"]], markets, what)]


def _fixtures(src, to, markets, code_commit):
    d = _json(Path(src) / "fixture_cstar_s2.json"); what = "fixtures"
    _common(d, code_commit, None, what)
    _require(list(d.get("budget") or []) == list(TV._budgets(False)[0]), f"{what}: budget {d.get('budget')} is not the inner budget")
    _require(list(d.get("markets") or {}) == list(markets), f"{what}: markets {list(d.get('markets') or {})} are not {list(markets)}")
    for m, v in d["markets"].items():
        _require(set(v.get("attacks", {})) >= {"D2", "D2+H3", "X7-SC"} and "reference" in v, f"{what}: market {m} lacks attacks or a reference")
    _require(d["spec"].get("cred") == _promoted_cred(to), f"{what}: cred differs from the promoted comparator's")
    return [(Path(src) / "fixture_cstar_s2.json", "fixture_cstar_s2.json")]


def _family(cov: dict, fam: str, branch: str) -> None:
    f = cov.get(fam) or {}; what = f"coverage {fam}"
    _require("kappa_effective" in f, f"{what}: no kappa_effective")
    _require(f.get("selection_replications") == REGISTERED["selection"], f"{what}: {f.get('selection_replications')} selection replications, not 10,000")
    _require(f.get("resamples") == REGISTERED["resamples"], f"{what}: {f.get('resamples')} resamples, not 9,999")
    ke = f["kappa_effective"]
    if ke is None:
        return
    v = f.get("validation") or {}
    _require(f.get("validation_replications") == REGISTERED["validation"] and v.get("replications", REGISTERED["validation"]) == REGISTERED["validation"],
             f"{what}: {f.get('validation_replications')} validation replications, not 20,000")
    _require(ke in KAPPAS and ke == f.get("kappa") == v.get("kappa"), f"{what}: kappa_effective {ke} is not the selected and validated kappa")
    want = [(e["fixture"], e["stat"], e["side"], e["alpha_e"]) for e in CAL.endpoints(fam, branch)]
    rows = v.get("endpoints") or []
    _require([(r.get("fixture"), r.get("stat"), r.get("side"), r.get("alpha_e")) for r in rows] == want, f"{what}: the validation endpoints are not the registered endpoint set")
    conf = 1.0 - 0.01 / CAL.denominator(fam)
    uppers = [clopper_pearson_upper(int(r["misses"]), REGISTERED["validation"], conf) for r in rows]
    admitted = all(u <= r["alpha_e"] for u, r in zip(uppers, rows))
    _require(admitted == bool(f.get("admitted")) == bool(v.get("admitted")) and admitted, f"{what}: recomputed admission {admitted} disagrees with the record")
    _require(all(abs(u - float(r["upper"])) < 1e-12 for u, r in zip(uppers, rows)), f"{what}: an endpoint's upper bound differs from its recomputation (admission)")


def _coverage(src, to, markets, code_commit, branch):
    _require(branch is not None, "coverage: --branch is required")
    cov = _json(Path(src) / "coverage.json"); what = "coverage"
    _require(cov.get("smoke") is False, f"{what}: smoke outputs are not promoted")
    _require(cov.get("commit") == code_commit, f"{what}: commit {cov.get('commit')!r} differs from the code commit {code_commit!r}")
    _require(cov.get("branch") == branch, f"{what}: branch {cov.get('branch')!r} is not {branch!r}")
    bm = list(CAL.BRANCHES[branch][0])
    _require(cov.get("markets") == bm == list(markets), f"{what}: markets {cov.get('markets')} are not the branch's {bm}")
    M = CAL.BRANCHES[branch][1]
    _require(cov.get("pool_size") == M, f"{what}: pool size {cov.get('pool_size')} is not the branch's {M}")
    for fam in ("Q1", "Q4"):
        _family(cov, fam, branch)
    prom = _promotion(to)["entries"]
    tuning = {p: h for p, h in prom.items() if p == "comparator.json" or p.startswith("log/") or p == "fixture_cstar_s2.json"}
    _require(cov.get("inputs_manifest") == tuning, f"{what}: the pools' inputs differ from the promoted tuning files")
    files = [(Path(src) / "coverage.json", "coverage.json")]
    for m in bm:
        p = Path(src) / "pools" / f"{m}.json"
        _require(p.exists() and _sha(p) == (cov.get("pools") or {}).get(m, {}).get("sha256"), f"{what}: pool {m} is missing or its hash differs")
        pl = _json(p)
        _require(pl.get("commit") == code_commit and pl.get("market") == m and pl.get("branch") == branch and pl.get("inputs_manifest") == cov.get("inputs_manifest"),
                 f"{what}: pool {m} has commit {pl.get('commit')!r}, market {pl.get('market')!r}, branch {pl.get('branch')!r}, or inputs other than the coverage's")
        _require(pl["seeds"] == coverage_pool(m, M), f"{what}: pool {m}'s seeds are not the registered coverage pool")
        _require(all(len(v) == M for v in list(pl["normalized"].values()) + list(pl["eff"].values())), f"{what}: pool {m} has a profile of the wrong length")
        files.append((p, f"pools/{m}.json"))
    return files


def _close(a, b) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_close(a[k], b[k]) for k in a)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)))
    return a == b


def _benchmark(src, to, markets, code_commit):
    raw = _json(Path(src) / "timings.json"); t = raw["timings"]; what = "benchmark"
    _require(raw.get("smoke") is False and t.get("smoke") is False, f"{what}: smoke outputs are not promoted")
    _require(t.get("commit") == code_commit, f"{what}: commit {t.get('commit')!r} differs from the code commit")
    _require(t.get("markets") == BENCH_MARKETS == list(markets), f"{what}: markets {t.get('markets')} are not {BENCH_MARKETS}")
    _require(int(t.get("vcpu") or 0) > 0 and float(t.get("usd_per_pod_hour") or 0) > 0, f"{what}: vcpu and usd_per_pod_hour must be recorded")
    table = json.loads(json.dumps(BV.cost_table(t, vcpu=int(t["vcpu"])), default=float))
    _require(_close(table, _json(Path(src) / "cost_table.json")), f"{what}: the cost table differs from its recomputation")
    return [(Path(src) / "timings.json", "benchmark/timings.json"), (Path(src) / "cost_table.json", "benchmark/cost_table.json")]


def _decision(src, to, markets, code_commit):
    d = _json(Path(src) / "decision.json"); what = "decision"
    tm = Path(to) / "benchmark" / "timings.json"
    _require(tm.exists(), f"{what}: the benchmark is not promoted yet")
    _require(d.get("timings_sha256") == _sha(tm), f"{what}: it was not decided on the promoted timings")
    t = _json(tm)["timings"]
    _require(_close(json.loads(json.dumps(BV.choose(t, d["ledger"], vcpu=int(t.get("vcpu") or 16)), default=float)), d["decision"]),
             f"{what}: the decision differs from its recomputation")
    return [(Path(src) / "decision.json", "benchmark/decision.json")]


CHECKS = {"comparator": _comparator, "system": _system, "fixtures": _fixtures, "benchmark": _benchmark, "decision": _decision}


def promote(kind: str, src, to, markets: list[str], branch: str | None = None, code_commit: str | None = None) -> list[str]:
    code_commit = code_commit or head(); Path(to).mkdir(parents=True, exist_ok=True)
    files = _coverage(src, to, markets, code_commit, branch) if kind == "coverage" else CHECKS[kind](src, to, markets, code_commit)
    return _record(to, kind, files)


def verify_promoted(to) -> list[str]:
    """Every promoted entry still matches its file: nothing changes between promotion, --final, and the lock."""
    to = Path(to); out = []
    for rel, h in _promotion(to)["entries"].items():
        f = to / rel
        if not f.exists():
            out.append(f"promoted {rel} is missing")
        elif _sha(f) != h:
            out.append(f"promoted {rel}: its hash differs from promotion.json")
    return out


def derive_params(to) -> dict:
    to = Path(to)
    return {"cred": _json(to / "comparator.json")["cred"], "tuned": {s: _json(to / f"tuned_{s}.json")["best_params"] for s in SYSTEMS}}


def final(to) -> dict:
    to = Path(to); prom = _promotion(to)
    need = ["comparator.json", "fixture_cstar_s2.json", "coverage.json", "benchmark/timings.json", "benchmark/decision.json"] + [f"tuned_{s}.json" for s in SYSTEMS]
    missing = [p for p in need if p not in prom["entries"]]
    _require(not missing, f"final: missing {missing}")
    changed = verify_promoted(to)
    _require(not changed, f"final: {changed}")
    params = derive_params(to)
    (to / "params.json").write_text(json.dumps(params, indent=1, sort_keys=True))
    return params


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["comparator", "system", "fixtures", "coverage", "benchmark", "decision"]); ap.add_argument("--from", dest="src")
    ap.add_argument("--to", default="experiments/v2"); ap.add_argument("--markets", default="headline,dev0,dev1"); ap.add_argument("--branch", default=None)
    ap.add_argument("--code-commit", dest="code_commit", default=None); ap.add_argument("--final", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.final:
            print(json.dumps(final(a.to), sort_keys=True))
        else:
            print("\n".join(promote(a.kind, a.src, a.to, a.markets.split(","), a.branch, a.code_commit)))
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
