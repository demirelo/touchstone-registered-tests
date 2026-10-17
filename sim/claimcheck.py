"""The claim predicate and decision rule (spec 8) and the lock, freeze, record, summary, coverage-report, and
proposed-module checks (spec 6 and 12)."""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .coverage import endpoint_key
from .describe import uses_not_expressible
from .intervals import bound
from .locked import settings_hash
from .sealed import bundle_hash, verify_patches

PASS, FAIL, INCONCLUSIVE = "PASS", "FAIL", "INCONCLUSIVE"
BASELINES = ("B2", "B3")
FROZEN_AT_FREEZE = ("sim/mechanisms/proposed.py", "experiments/proposed.yaml", "experiments/proposed_describe.yaml")
ALLOWED_IMPORTS = ("sim.mechanisms.base", "numpy", "scipy", "math", "dataclasses", "typing", "__future__", "itertools", "functools")
FROZEN_MODULES = ("sim.market", "sim.mechanisms.base", "sim.policies.base", "sim.policies.honest", "sim.policies.twin", "sim.metrics", "sim.rng")
FROZEN_EXTERNAL = ("numpy", "numpy.random", "numpy.linalg", "scipy.stats", "scipy.special", "math", "random")
BANNED_ATTRS = ("__subclasses__", "__globals__", "__builtins__", "__dict__", "__base__", "__bases__", "__mro__", "__class__", "__code__", "__closure__", "__loader__", "__spec__")


@dataclass
class Verdict:
    status: str
    bound: float | None
    side: str | None
    method: str | None
    threshold: float
    n: int
    note: str = ""


def _inc(n: int, note: str, threshold: float = 0.0) -> Verdict:
    return Verdict(INCONCLUSIVE, None, None, None, threshold, n, note)


def _admitted(coverage: dict, stat: str, side: str, level: float, n: int):
    return coverage["admitted_sides"].get(endpoint_key(stat, side, level, n))


def decide(x, stat: str, pass_side: str, level: float, threshold: float, coverage: dict, settings: dict, n: int | None = None) -> Verdict:
    x = np.asarray(x, dtype=float); n = int(x.size if n is None else n)
    if x.size != n or x.size < 2:
        return _inc(n, f"{x.size} observations, expected {n}", threshold)
    opp = "upper" if pass_side == "lower" else "lower"
    m_pass = _admitted(coverage, stat, pass_side, level, n)
    if m_pass is not None:
        b = bound(m_pass, x, pass_side, level, settings)
        if (b.value >= threshold) if pass_side == "lower" else (b.value <= threshold):
            return Verdict(PASS, b.value, pass_side, m_pass, threshold, n, "degenerate" if b.degenerate else "")
    m_opp = _admitted(coverage, stat, opp, level, n)
    if m_opp is not None:
        b2 = bound(m_opp, x, opp, level, settings)
        if (b2.value < threshold) if pass_side == "lower" else (b2.value > threshold):
            return Verdict(FAIL, b2.value, opp, m_opp, threshold, n, "degenerate" if b2.degenerate else "")
    note = f"{pass_side} side not admitted at n = {n}" if m_pass is None else "the pass side did not clear and the opposite side did not miss"
    return Verdict(INCONCLUSIVE, None, None, m_pass, threshold, n, note)


def combine_all(statuses) -> str:
    s = list(statuses)
    return PASS if s and all(v == PASS for v in s) else FAIL if any(v == FAIL for v in s) else INCONCLUSIVE


def combine_any(statuses) -> str:
    s = list(statuses)
    return PASS if any(v == PASS for v in s) else FAIL if s and all(v == FAIL for v in s) else INCONCLUSIVE


def h1_frame(h1_rows: pd.DataFrame) -> pd.DataFrame:
    f = h1_rows.rename(columns={"eval_seed": "seed"}).copy(); f["family"] = "H1"
    return f


def h1_cell_reason(rule: str, h1_summary: dict | None, beta: float) -> str | None:
    if h1_summary is None:
        return "missing"
    cell = h1_summary.get("cells", {}).get(f"{rule}|{beta}")
    if cell is None:
        return "missing"
    return "invalid repetitions" if cell.get("inconclusive") else None


def h1_proposed_reason(proposed: str, h1_summary: dict | None, describe_record: dict | None, beta: float) -> str | None:
    """Ruling D11: comprehension is compared with the minimum of B2's and B3's scores."""
    if describe_record is not None and uses_not_expressible(describe_record):
        return "not expressible"
    if h1_summary is not None:
        comp = h1_summary.get("comprehension", {}); others = [comp[b] for b in BASELINES if b in comp]
        if proposed in comp and others and comp[proposed] < min(others) - 1:
            return "comprehension"
    return h1_cell_reason(proposed, h1_summary, beta)


def required_families(coverage: dict) -> list:
    return ["H2"] + (["H1"] if coverage["consequences"].get("h1") == "confirmatory" else [])


def _rows(df: pd.DataFrame | None, rule: str, beta: float, position: str | None) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    d = df[df["rule"] == rule]
    if "beta" in d:
        d = d[np.isclose(d["beta"].astype(float), beta)]
    if position is not None and "position" in d:
        d = d[d["position"] == position]
    return d.sort_values("seed").reset_index(drop=True)


def evaluate_claim(h2: pd.DataFrame | None, h1: pd.DataFrame | None, coverage: dict, locked: dict, proposed: str, h1_summary: dict | None = None,
                   describe_record: dict | None = None, h2_headline: dict | None = None, demoted=frozenset()) -> dict:
    c = locked["claim"]; beta = float(c["beta"]); settings = locked["intervals"]; cons = coverage["consequences"]; headline = h2_headline or {}
    confirmatory = required_families(coverage)
    frames = {"H2": h2, "H1": h1_frame(h1) if h1 is not None else None}
    n_of = {"H2": int(cons["final_eval_n"]) if cons.get("final_eval_n") else None, "H1": int(locked["intervals"]["h1_repetitions"])}
    h1_note = h1_proposed_reason(proposed, h1_summary, describe_record, beta) if "H1" in confirmatory else ("exploratory (proxy bound not admitted)" if h1 is not None else None)
    rl, bl = float(c["rule_level"]), float(c["baseline_level"])

    def blocked(fam: str, rule: str) -> str | None:
        if f"{rule}|{fam}" in demoted:
            return "demoted by a logged repair"
        if fam == "H2" and n_of["H2"] is None:
            return "parametrized bound not admitted at any n"
        if fam == "H1":
            return h1_note if rule == proposed else h1_cell_reason(rule, h1_summary, beta)
        return None

    def rows_for(fam: str, rule: str) -> pd.DataFrame:
        return _rows(frames[fam], rule, beta, headline.get(rule, "median") if fam == "H2" else None)

    rule_clause = {}
    for fam in confirmatory:
        n = n_of[fam] or 0; why = blocked(fam, proposed); d = rows_for(fam, proposed)
        if why is None and len(d) == 0:
            why = "no rows"
        if why is not None:
            v = _inc(n, f"{fam} inconclusive: {why}")
            rule_clause[fam] = {"eff": v, "gain": v, "audit": INCONCLUSIVE, "status": INCONCLUSIVE, "audit_over_sstar_mean": None}
            continue
        eff = decide(d["eff_attack"], "eff", "lower", rl, float(c["eff_min"]), coverage, settings, n)
        gain = decide(d["gain"], "gain", "upper", rl, float(c["gain_max"]), coverage, settings, n)
        audit = PASS if len(d) == n and bool((d["audit_cost_attack"] <= d["budget"] + 1e-9).all()) else FAIL if len(d) == n else INCONCLUSIVE
        rule_clause[fam] = {"eff": eff, "gain": gain, "audit": audit, "status": combine_all([eff.status, gain.status, audit]),
                            "audit_over_sstar_mean": float((d["audit_cost_attack"] / d["sstar"]).mean())}
    baseline_clause = {}
    for B in BASELINES:
        pairs = {}
        for fam in confirmatory:
            n = n_of[fam] or 0; why = blocked(fam, B) or blocked(fam, proposed)
            dB = rows_for(fam, B); dR = rows_for(fam, proposed)
            if why is None and (len(dB) == 0 or len(dR) == 0):
                why = "no rows"
            if why is not None:
                pairs[f"{fam}|loss_diff"] = pairs[f"{fam}|gain"] = _inc(n, f"{fam} inconclusive: {why}")
                continue
            m = dB.merge(dR, on="seed", suffixes=("_B", "_R"))
            ld = (m["eff_clip_B"] - m["eff_attack_B"]) - (m["eff_clip_R"] - m["eff_attack_R"])
            pairs[f"{fam}|loss_diff"] = decide(ld, "loss_diff", "lower", bl, float(c["loss_diff_min"]), coverage, settings, n)
            pairs[f"{fam}|gain"] = decide(dB["gain"], "gain", "lower", bl, float(c["baseline_gain_min"]), coverage, settings, n)
        baseline_clause[B] = {"pairs": pairs, "status": combine_any([v.status for v in pairs.values()])}
    statuses = [v["status"] for v in rule_clause.values()] + [v["status"] for v in baseline_clause.values()]
    return {"claim": combine_all(statuses), "confirmatory": confirmatory, "rule_clause": rule_clause, "baseline_clause": baseline_clause, "h1_note": h1_note,
            "n": {k: v for k, v in n_of.items() if k in confirmatory}, "demoted": sorted(demoted), "proposed": proposed, "beta": beta}


def evaluate_amendment(h3: pd.DataFrame | None, cov_base: dict, cov_ext: dict | None, locked: dict, amend: dict, proposed: str, h2_rule_status: str,
                       demoted=frozenset()) -> dict:
    """Amendment 1: the H3 comparative clause (public identity-replacement stress test on fresh final-evaluation seeds).
    Absolute part on R*: eff lower 95% >= eff_min, gain upper 95% <= gain_max, audit <= B every seed (bounds from the base
    study's admitted sides at n). Comparative part per baseline: paired gain(B) - gain(R*) lower 98.75% >= gain_reduction_min
    PASS, upper 98.75% < it FAIL, else INCONCLUSIVE; PASS needs both baselines, FAIL any. Amended PASS also needs the
    original H2 rule clause PASS and the gain_diff sides admitted by the extension report."""
    from .amendment import LIMITATION
    c = amend["clause"]; n = int(c["n"]); beta = float(c["beta"]); fam = c.get("family", "D2+H3"); pos = c.get("position", "median")
    settings = locked["intervals"]; rl, bl = float(c["level_rule"]), float(c["level_comparative"])
    out = {"amended": INCONCLUSIVE, "h2_rule_status": h2_rule_status, "absolute": {}, "comparative": {}, "admitted": False, "n": n, "note": LIMITATION, "reason": ""}
    admitted = cov_ext is not None and (cov_ext.get("consequences") or {}).get("h3_comparative") == "confirmatory" \
        and all(cov_ext.get("admitted_sides", {}).get(endpoint_key("gain_diff", side, bl, n)) for side in ("lower", "upper"))
    out["admitted"] = bool(admitted)
    if not admitted:
        out["reason"] = "gain_diff sides not admitted by the extension report"; return out
    if h3 is None or len(h3) == 0:
        out["reason"] = "no H3 rows"; return out
    rows = {}
    for rule in [proposed] + list(c["baselines"]):
        if f"{rule}|{fam}" in demoted:
            out["reason"] = f"{rule}|{fam} demoted by a logged repair"; return out
        d = _rows(h3[h3["family"] == fam] if "family" in h3 else h3, rule, beta, pos)
        if len(d) != n or d["seed"].nunique() != n:
            out["reason"] = f"{rule}: rows {len(d)} with {d['seed'].nunique() if len(d) else 0} unique seeds, expected {n}"; return out
        rows[rule] = d
    dR = rows[proposed]
    eff = decide(dR["eff_attack"], "eff", "lower", rl, float(c["eff_min"]), cov_base, settings, n)
    gain = decide(dR["gain"], "gain", "upper", rl, float(c["gain_max"]), cov_base, settings, n)
    audit = PASS if bool((dR["audit_cost_attack"] <= dR["budget"] + 1e-9).all()) else FAIL
    out["absolute"] = {"eff": eff, "gain": gain, "audit": audit, "status": combine_all([eff.status, gain.status, audit]),
                       "audit_over_sstar_mean": float((dR["audit_cost_attack"] / dR["sstar"]).mean())}
    comp = {}
    for B in c["baselines"]:
        m = rows[B].merge(dR, on="seed", suffixes=("_B", "_R"))
        if len(m) != n:
            out["reason"] = f"{B}: pairing with {proposed} on seed gives {len(m)} rows, expected {n}"; return out
        comp[B] = decide(m["gain_B"] - m["gain_R"], "gain_diff", "lower", bl, float(c["gain_reduction_min"]), cov_ext, settings, n)
    statuses = [v.status for v in comp.values()]
    comp["status"] = PASS if all(x == PASS for x in statuses) else FAIL if any(x == FAIL for x in statuses) else INCONCLUSIVE
    out["comparative"] = comp
    out["amended"] = combine_all([h2_rule_status, out["absolute"]["status"], comp["status"]])
    return out


def verify_h3_records(records, locked: dict, jobs: dict, expected_seeds, proposed: str) -> list:
    """The final H3 records: the common record check, no duplicate seed inside a record, every required rule present."""
    problems = verify_records(records, locked, jobs, expected_seeds)
    for rec in records:
        name = rec.get("spec", {}).get("name", "?"); seeds = [int(r.get("seed")) for r in rec.get("rows", [])]
        if len(set(seeds)) != len(seeds):
            problems.append(f"{name}: duplicate seed in the rows")
    have = {rec.get("spec", {}).get("rule") for rec in records}
    for rule in list(BASELINES) + [proposed]:
        if rule not in have:
            problems.append(f"missing rule {rule}: no H3 record")
    return problems


def verify_amendment_report(path, amend: dict) -> list:
    """The extension report named by the amendment: its hash, a registered (non-smoke) admission, the six registered cells, the
    consequences recorded in the amendment, and the limitation sentence."""
    from .amendment import LIMITATION
    data = Path(path).read_bytes(); problems = []
    if hashlib.sha256(data).hexdigest() != amend.get("coverage_report_amendment_sha256"):
        problems.append("amendment report: hash differs from the amendment's coverage_report_amendment_sha256")
    rep = json.loads(data)
    if rep.get("admission_basis") != "registered" or rep.get("smoke"):
        problems.append("amendment report: not a registered admission")
    names = [c.get("name") for c in rep.get("selection", [])]
    reg_path = Path(__file__).resolve().parents[1] / "experiments" / "coverage_cells.json"
    registered = [c.get("name") for c in json.loads(reg_path.read_text())] if reg_path.exists() else []
    if len(names) != 6 or len(set(names)) != 6 or not all(names) or (registered and names != registered):
        problems.append("amendment report: selection is not the six registered cells")
    if rep.get("consequences") != amend.get("coverage_consequences"):
        problems.append("amendment report: consequences differ from the amendment")
    if rep.get("limitation") != LIMITATION:
        problems.append("amendment report: the limitation sentence is missing or altered")
    return problems


def verdict_json(result: dict) -> dict:
    def conv(v):
        if isinstance(v, Verdict):
            return asdict(v)
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        return v
    return conv(result)


# ---- lock, freeze, record, summary, report, and module checks -----------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def tree_changes(repo: Path, ref: str, paths=None) -> dict:
    """Working tree against `ref`: {path: 'M' | 'A' | 'D'} (git handles quoting, symlinks, and the index)."""
    out = _git(repo, "diff", "--name-status", "-z", "--no-renames", ref, "--", *(paths or [])).split("\0")
    changes = {}
    for status, path in zip(out[0::2], out[1::2]):
        if status:
            changes[path] = status[0]
    return changes


def allowed(path: str, allow_list) -> bool:
    return any(path == e or (e.endswith("/") and path.startswith(e)) for e in allow_list)


def verify_lock(repo, lock_tag: str, allow_list) -> list:
    words = {"M": "changed", "A": "new tracked file", "D": "deleted"}
    return [f"{path}: {words.get(st, st)} since {lock_tag} and outside the allow-list" for path, st in sorted(tree_changes(Path(repo), lock_tag).items()) if not allowed(path, allow_list)]


def verify_freeze(repo, freeze_tag: str, locked: dict, allow_list) -> list:
    repo = Path(repo); problems = []
    in_tag = {e.split("\t", 1)[1] for e in _git(repo, "ls-tree", "-r", "-z", freeze_tag).split("\0") if e}
    for path in FROZEN_AT_FREEZE:
        if path not in in_tag:
            problems.append(f"{path}: missing from the freeze tag {freeze_tag}")
    changed = tree_changes(repo, freeze_tag, list(FROZEN_AT_FREEZE))
    for path, st in changed.items():
        problems.append(f"{path}: {'deleted' if st == 'D' else 'differs'} since the freeze tag {freeze_tag}")
    sealed = repo / "sealed"
    if not sealed.exists():
        problems.append("sealed/: missing")
    else:
        want = locked.get("sealed_bundle_sha256"); got = bundle_hash(sealed)
        if want != got:
            problems.append(f"sealed/: bundle hash {got} differs from the lock commitment {want}")
        problems += verify_patches(sealed)
    return problems


def verify_records(records, locked: dict, jobs: dict, expected_seeds) -> list:
    """Every held-out record is checked by the sweep's own check_record against the job rebuilt from the lock (params,
    cfg, settings hash, budget, smoke, salt), then for the namespace, the bundle hash, and the exact seed sequence."""
    from scripts.sweep import check_record
    problems = []; n_final = int((locked.get("coverage_consequences") or {}).get("final_eval_n") or 0)
    want_seeds = [int(x) for x in expected_seeds][:n_final]
    for rec in records:
        name = rec.get("spec", {}).get("name", "?")
        job = jobs.get(name)
        if job is None:
            problems.append(f"{name}: no job for this record in the locked manifest"); continue
        try:
            check_record(job, rec)
        except SystemExit as e:
            problems.append(f"{name}: {e}")
        if rec.get("eval_namespace") != "final_eval":
            problems.append(f"{name}: evaluation namespace is {rec.get('eval_namespace')!r}, not final_eval")
        if rec.get("spec", {}).get("family") == "H2" and rec.get("bundle_hash") != locked.get("sealed_bundle_sha256"):
            problems.append(f"{name}: bundle hash differs from the lock commitment")
        if rec.get("salt_hash") != locked.get("identity_salt_sha256"):
            problems.append(f"{name}: salt hash differs from the lock commitment")
        seeds = [int(r.get("seed")) for r in rec.get("rows", [])]
        if seeds != want_seeds:
            problems.append(f"{name}: row seeds are not the first {n_final} sealed final-eval seeds in order")
        spec = job["spec"]; want_meta = {"rule": spec["rule"], "family": spec["family"], "beta": float(spec["beta"]), "position": spec["position"], "budget": float(job["cfg"]["budget"])}
        for r in rec.get("rows", []):
            got = {k: (float(r.get(k)) if k in ("beta", "budget") else r.get(k)) for k in want_meta}
            if got != want_meta:
                problems.append(f"{name}: a row's metadata {got} differs from the job {want_meta}"); break
    return problems


def verify_h1_summary(summary: dict, rows: pd.DataFrame, locked: dict, prompt_path, expected_seeds) -> list:
    h = locked["h1"]; problems = []; reps = int(locked["intervals"]["h1_repetitions"]); want = [int(x) for x in expected_seeds][:reps]
    if summary.get("model") != h["model"]:
        problems.append(f"h1 summary: model {summary.get('model')!r} is not the sealed LLM {h['model']!r}")
    if int(summary.get("T", -1)) != int(h["T"]):
        problems.append(f"h1 summary: T = {summary.get('T')}, locked h1.T = {h['T']}")
    if summary.get("eval_namespace") != "final_eval":
        problems.append("h1 summary: evaluation namespace is not final_eval")
    want_prompt = hashlib.sha256(Path(prompt_path).read_bytes()).hexdigest() if Path(prompt_path).exists() else None
    if summary.get("instructions_sha256") != want_prompt:
        problems.append("h1 summary: the instructions hash is not the sealed prompt's hash")
    if summary.get("calibration_t100_sha256") != (locked.get("calibration") or {}).get("T100", {}).get("sha256"):
        problems.append("h1 summary: the T = 100 calibration hash differs from the lock")
    if summary.get("smoke"):
        problems.append("h1 summary: smoke run")
    if summary.get("partial"):
        problems.append(f"h1 summary: partial cells {summary['partial']}")
    for r, hsh in (locked.get("tuned") or {}).items():
        if r in set(rows["rule"]) and summary.get("tuned_sha256", {}).get(r) != hsh:
            problems.append(f"h1 summary: tuned file hash for {r} differs from the lock")
    comp = summary.get("comprehension", {})
    if not all(k in comp for k in list(BASELINES) + [r for r in rows["rule"].unique() if r not in BASELINES]):
        problems.append("h1 summary: comprehension scores missing for a rule in the rows")
    limit = int(h["invalid_limit"])
    for (rule, beta), d in rows.groupby(["rule", "beta"]):
        d = d.sort_values("rep")
        if list(d["rep"]) != list(range(reps)) or [int(x) for x in d["eval_seed"]] != want:
            problems.append(f"h1 rows {rule}|{beta}: repetitions or evaluation seeds are not the first {reps} sealed seeds in order")
        raw = d["invalid"].tolist()
        if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and float(v) in (0.0, 1.0) for v in raw):
            problems.append(f"h1 rows {rule}|{beta}: invalid flags are not binary")
        if "T" not in d or "model" not in d:
            problems.append(f"h1 rows {rule}|{beta}: rows lack the T or model column")
        else:
            if not (d["T"].astype(int) == int(h["T"])).all():
                problems.append(f"h1 rows {rule}|{beta}: T differs from locked h1.T")
            if not (d["model"] == h["model"]).all():
                problems.append(f"h1 rows {rule}|{beta}: model differs from the sealed LLM")
        cell = summary.get("cells", {}).get(f"{rule}|{beta}")
        count = int(d["invalid"].sum())
        if cell is None or count != int(cell.get("invalid_count", -1)):
            problems.append(f"h1 rows {rule}|{beta}: invalid flags do not match the summary")
        elif bool(cell.get("inconclusive")) != (count > limit):
            problems.append(f"h1 rows {rule}|{beta}: the summary's inconclusive flag contradicts {count} invalid repetitions against the limit {limit}")
    return problems


def verify_coverage_report(path, locked: dict) -> list:
    data = Path(path).read_bytes(); problems = []
    if hashlib.sha256(data).hexdigest() != locked.get("coverage_report_sha256"):
        problems.append("coverage report: hash differs from the lock")
    rep = json.loads(data)
    if rep.get("admission_basis") != "registered" or rep.get("smoke"):
        problems.append("coverage report: not a registered admission")
    names = [c.get("name") for c in rep.get("selection", [])]
    if len(names) != 6 or len(set(names)) != 6 or not all(names):
        problems.append("coverage report: selection is not 6 distinct named cells")
    if rep.get("consequences") != locked.get("coverage_consequences"):
        problems.append("coverage report: consequences differ from the lock")
    return problems


def _snapshot() -> dict:
    """Every loaded sim.* module: module attributes, class attributes, and function internals (code, defaults, dict)."""
    import sys as _sys, types
    out = {}
    def fn_sig(f):
        return (id(getattr(f, "__code__", None)), repr(getattr(f, "__defaults__", None)), repr(getattr(f, "__kwdefaults__", None)), repr(sorted(getattr(f, "__dict__", {}).items(), key=str)))
    def val(v):
        if isinstance(v, (types.FunctionType, types.MethodType, staticmethod, classmethod)):
            return ("fn", fn_sig(getattr(v, "__func__", v)))
        if isinstance(v, (int, float, str, tuple, bool, type(None), frozenset)):
            return ("val", repr(v))
        return ("id", id(v))
    for m, mod in list(_sys.modules.items()):
        if not (m == "sim" or m.startswith("sim.") or m in FROZEN_EXTERNAL) or mod is None:
            continue
        for k, v in list(vars(mod).items()):
            if k.startswith("__"):
                continue
            out[(m, k)] = val(v)
            if isinstance(v, type) and getattr(v, "__module__", None) == m:
                for ak, av in list(vars(v).items()):
                    if ak not in ("__dict__", "__weakref__", "__module__", "__doc__", "__annotations__"):     # constructors and other behavior-bearing dunders count
                        out[(m, f"{k}.{ak}")] = val(av)
    return out


def check_proposed_module(path, repo, params: dict | None = None) -> list:
    """Spec 12: proposed.py imports only sim/mechanisms/base.py (absolute form) and standard numerical libraries, and
    neither importing it nor calling make(params) changes any attribute of a loaded sim.* module (functions compared by
    code, defaults, and dict). A detected change is reported and restored where the original is known."""
    import sys as _sys
    problems = []; src = Path(path).read_text(); tree = ast.parse(src)
    aliases = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            aliases |= {(a.asname or a.name.split(".")[0]) for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            aliases |= {(a.asname or a.name) for a in node.names}
    def root_name(t):
        while isinstance(t, (ast.Attribute, ast.Subscript)):
            t = t.value
        return t.id if isinstance(t, ast.Name) else None
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, (ast.Assign,)):
            targets = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        elif isinstance(node, ast.Delete):
            targets = node.targets
        for t in targets:
            if isinstance(t, (ast.Attribute, ast.Subscript)) and root_name(t) in aliases:
                problems.append(f"{Path(path).name}: attribute assignment on the imported name {root_name(t)!r} is not allowed (monkeypatching)")
        if isinstance(node, ast.Call):
            f = node.func; fname = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            root = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
            dunder_arg = fname in ("getattr", "setattr", "delattr") and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and str(node.args[1].value).startswith("__")
            nonliteral_attr = fname in ("getattr", "setattr", "delattr") and len(node.args) >= 2 and not isinstance(node.args[1], ast.Constant)
            if fname in ("__import__", "exec", "eval", "compile", "globals", "vars") or dunder_arg or nonliteral_attr or root in ("importlib", "builtins", "sys") or fname in ("import_module", "spec_from_file_location", "exec_module"):
                problems.append(f"{Path(path).name}: dynamic import or reflection ({fname}) is not allowed")
        if isinstance(node, ast.Name) and node.id in ("__builtins__", "__import__"):
            problems.append(f"{Path(path).name}: use of {node.id} is not allowed")
        if isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRS:
            problems.append(f"{Path(path).name}: access to {node.attr} is not allowed")
        if isinstance(node, ast.ImportFrom) and node.level:
            problems.append(f"{Path(path).name}: relative import is not allowed (use absolute imports)"); continue
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        for name in names:
            if not any(name == ok or name.startswith(ok + ".") for ok in ALLOWED_IMPORTS):
                problems.append(f"{Path(path).name}: import of {name!r} is not allowed (only {', '.join(ALLOWED_IMPORTS)})")
    for m in FROZEN_MODULES + ("sim.mechanisms.posted", "sim.mechanisms.posted_audit", "sim.mechanisms.second_score") + FROZEN_EXTERNAL:
        importlib.import_module(m)
    originals = {(m, k): v for m, mod in list(_sys.modules.items()) if (m == "sim" or m.startswith("sim.") or m in FROZEN_EXTERNAL) and mod is not None for k, v in list(vars(mod).items())}
    class_originals = {(m, f"{k}.{ak}"): av for (m, k), v in originals.items() if isinstance(v, type) and getattr(v, "__module__", None) == m for ak, av in list(vars(v).items())}
    before = _snapshot()
    spec = importlib.util.spec_from_file_location("proposed_under_check", path); mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        if params is not None and callable(getattr(mod, "make", None)):
            mod.make(dict(params))
    except Exception as e:                                        # an import or factory error is a problem, not a crash of the checker
        problems.append(f"{Path(path).name}: import or make() failed: {e!r}")
    after = _snapshot()
    for key in sorted(set(before) | set(after), key=str):
        if before.get(key) != after.get(key):
            m, k = key; problems.append(f"{m}.{k}: changed by {Path(path).name}")
            if "." in k and (m, k) in class_originals:
                cls, attr = k.split(".", 1); setattr(originals[(m, cls)], attr, class_originals[(m, k)])   # a replaced class attribute is restored
            elif "." not in k and (m, k) in originals:
                setattr(_sys.modules[m], k, originals[(m, k)])    # a replaced module attribute is restored
            elif "." not in k and k in vars(_sys.modules[m]):
                delattr(_sys.modules[m], k)                       # an attribute added by the module is removed
            # a changed class attribute or function internal cannot be restored from a snapshot of ids: the report is the
            # guarantee, and check_claim.py refuses the run
    return problems


def check_proposed_module_isolated(path, repo, params: dict | None = None) -> list:
    """The same check in a subprocess, so the verdict process never imports the proposed module (a module that passes the
    source rules could still change numpy or scipy state for the process that imported it)."""
    import subprocess, sys as _sys
    code = ("import json, sys; sys.path.insert(0, %r); from sim.claimcheck import check_proposed_module; "
            "print(json.dumps(check_proposed_module(%r, %r, params=json.loads(%r))))") % (str(repo), str(path), str(repo), json.dumps(params) if params is not None else "null")
    r = subprocess.run([_sys.executable, "-c", code], cwd=str(repo), capture_output=True, text=True)
    if r.returncode != 0:
        return [f"{Path(path).name}: the isolated module check crashed: {r.stderr.strip()[-400:]}"]
    try:
        return list(json.loads(r.stdout.strip().splitlines()[-1]))
    except (ValueError, IndexError):
        return [f"{Path(path).name}: the isolated module check gave no result: {r.stdout[-400:]}"]


def verify_describe_record(record: dict, rule) -> list:
    """The frozen proposed_describe.yaml must be a vocabulary record and equal the record of the rule the actor saw."""
    from .describe import DESCRIBE_FIELDS, describe_record, load_vocabulary, validate_record
    problems = []
    try:
        validate_record(record, load_vocabulary())
    except ValueError as e:
        problems.append(f"proposed_describe.yaml: {e}")
    want = describe_record(rule)
    for k in DESCRIBE_FIELDS + ("parameters",):
        if record.get(k) != want.get(k):
            problems.append(f"proposed_describe.yaml: field {k!r} is {record.get(k)!r}, the frozen rule's describe() says {want.get(k)!r}")
    return problems
