"""Numerical checks of the reset-deterrence package (docs/theory/reset-deterrence.md; plan Task 2). Fixed diagnostic
configurations run through the frozen harness; every theorem quantity is computed from the EpisodeResult (effort and
identities), its ledger (money per identity and round), the offers in its history (first-offer rounds), and, for R3, the
quota rebuilt from the configuration with the frozen schedule functions. Renewal formulas are applied only when their
assumptions are checked and hold; otherwise the result says `applicable: false` and names the failed assumptions."""
from __future__ import annotations

import argparse, json, math, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.mechanisms.proposed import audit_quota, terminal as r3_terminal

W = 10


def _phi(x: float) -> float:
    return math.exp(-x * x / 2) / math.sqrt(2 * math.pi)


def _Phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def detect(delta: float, tol: float, sigma: float) -> float:
    return _Phi((delta - tol) / sigma)


def round_table(res, cfg, rule_name: str, rule_params: dict, focal: int) -> list[dict]:
    T, N, J = cfg.T, cfg.N, cfg.J
    ent = list(res.entity_of); born = list(res.identity_round); gen = list(res.identity_generation)
    ids_f = [i for i, e in enumerate(ent) if e == focal]
    led = res.ledger; L = int(rule_params.get("L", 10)); tol = float(rule_params.get("tol", 0.16))
    first_offer: dict[int, int] = {}
    for rec in res.history:
        for i in rec.offers:
            first_offer.setdefault(int(i), int(rec.t))
    is_r3 = rule_name == "proposed"
    A_tot = int(math.floor(cfg.budget / cfg.alpha + 1e-12)) if cfg.alpha > 0 else 0
    carry = 0; used = 0; rows = []
    p = cfg.providers[focal]
    for rec in res.history:
        t = int(rec.t)
        active = max((i for i in ids_f if born[i] <= t), key=lambda i: (born[i], gen[i]))
        jobs_f = [j for j, i in rec.assignment.items() if ent[i] == focal]
        aud = {a.job for a in rec.audits}
        S = len(jobs_f); K = sum(1 for j in jobs_f if j in aud)
        pay = sum(float(rec.payments[j]) for j in jobs_f); apay = sum(float(rec.payments[j]) for j in jobs_f if j in aud)
        offered = active in rec.offers
        age = t - first_offer.get(active, born[active])
        if T - t <= L:
            phase = "terminal"
        elif not offered:
            phase = "banned"
        else:
            phase = "fresh" if age < W else "established"
        claim = float(rec.offers[active].claim) if offered else None
        bid = float(rec.offers[active].bid) if offered else None
        effort = float(res.efforts[t, focal]); delta = (claim - effort) if claim is not None else 0.0
        profit = float(sum(led.released[t, i] + led.holdback_out[t, i] - led.cost[t, i] - led.entry[t, i] for i in ids_f))
        row = {"t": t, "active": active, "generation": gen[active], "age": age, "phase": phase, "S": S, "K": K, "payment": pay,
               "audited_payment": apay, "failures": int(res.failures[t, focal]), "refunds": float(sum(led.refunds[t, i] for i in ids_f)),
               "entry": float(sum(led.entry[t, i] for i in ids_f)), "profit": profit, "claim": claim, "bid": bid, "effort": effort,
               "delta": delta, "d": detect(delta, tol, cfg.sigma), "d0": detect(0.0, tol, cfg.sigma), "b": p.b,
               "served_round": len(rec.assignment), "audits_round": len(rec.audits), "k_available": None, "carry": None,
               "audits_left": None, "H": None, "n": None, "k_prime": None, "group_audits": None, "k_available_capped": None}
        if is_r3:
            left = A_tot - used
            k_av = int(min(len(rec.assignment), A_tot)) if r3_terminal(t, T, L) else audit_quota(t, T, L, J, A_tot, carry)
            k = max(0, min(k_av, len(rec.assignment), left))
            row.update({"k_available": k_av, "carry": carry, "audits_left": left, "k_available_capped": k})
            if phase == "fresh" and S > 0:
                fr = first_offer.get(active, born[active])
                fresh_ids = {i for i in rec.offers if 0 <= t - first_offer.get(int(i), t) < L}
                H = sum(1 for j, i in rec.assignment.items() if i in fresh_ids and first_offer.get(i, t) > fr)
                n = sum(1 for j, i in rec.assignment.items() if i in fresh_ids and first_offer.get(i, t) == fr)
                row.update({"H": H, "n": n, "k_prime": min(n, max(0, k - H)),
                            "group_audits": sum(1 for j, i in rec.assignment.items() if j in aud and i in fresh_ids and first_offer.get(i, t) == fr)})
            carry = 0 if r3_terminal(t, T, L) else int(k_av - len(rec.audits)); used += len(rec.audits)
        rows.append(row)
    return rows


def hypergeom_pmf(n: int, s: int, k: int) -> np.ndarray:
    return np.array([math.comb(s, l) * math.comb(n - s, k - l) / math.comb(n, k) if 0 <= k - l <= n - s else 0.0 for l in range(s + 1)])


def hazard_from_K(rows: list, d: float) -> float:
    return float(np.mean([1 - (1 - d) ** r["K"] for r in rows])) if rows else float("nan")


def expected_recovery(r: float, L: int) -> float:
    if r >= 1.0:
        return float(L)
    return (1 - r ** L) / ((1 - r) * r ** L)


def renewal_profit(r_E: float, q_E: float, ER_F: float, ED: float, e_in: float, EN_R: float) -> float:
    return (r_E / q_E + ER_F - e_in * EN_R) / (1 / q_E + ED)


def surplus_bound(G_E: float, q_E: float, eps: float, L: int) -> float:
    return eps + max(0.0, G_E - eps) / (1 + q_E * L)


def surplus_terms(rows: list, tol: float, sigma: float) -> dict:
    """Shading surplus with the audited escrow (payment-weighted) against the per-job mean escrow times K (unweighted)."""
    pw = uw = 0.0
    for r in rows:
        d, d0 = detect(r["delta"], tol, sigma), detect(0.0, tol, sigma); g = r["b"] * r["delta"]
        pw += r["S"] * g - (d - d0) * r["audited_payment"]
        uw += r["S"] * g - (d - d0) * r["K"] * (r["payment"] / r["S"] if r["S"] else 0.0)
    return {"payment_weighted": pw / max(1, len(rows)), "unweighted": uw / max(1, len(rows))}


def terminal_margin(cfg, tol: float) -> dict:
    sub = cfg.v_max * _phi(tol / cfg.sigma) / cfg.sigma; bmin = min(p.b for p in cfg.providers)
    return {"subtracted_max": sub, "b_min": bmin, "profitable": bmin > sub}


def established_rates(rows: list) -> dict:
    out = {}
    for name, sel in (("initial", lambda r: r["generation"] == 0), ("replacement", lambda r: r["generation"] > 0)):
        rr = [r for r in rows if r["phase"] == "established" and sel(r) and r["S"] > 0]
        out[name] = {"rounds": len(rr), "K_per_S": (sum(r["K"] for r in rr) / sum(r["S"] for r in rr)) if rr else None}
    return out


def finite_horizon(rows: list, L: int) -> dict:
    T = len(rows)
    ini = sum(r["profit"] for r in rows if r["t"] < W); ter = sum(r["profit"] for r in rows if T - r["t"] <= L)
    mid = sum(r["profit"] for r in rows if r["t"] >= W and T - r["t"] > L)
    return {"initial": ini, "middle": mid, "terminal": ter, "per_round": (ini + mid + ter) / T}


def extract_cycles(rows: list) -> dict:
    """Complete cycles: an established spell ending in a round with a failure, then the recovery (every later round up to,
    not including, the next established round). Rounds before the first spell, an open final spell, and an unfinished
    recovery are censored. Restarts count failures inside the recovery."""
    rows = sorted(rows, key=lambda r: r["t"]); complete = []; i = 0; n = len(rows); used = set()
    while i < n:
        if rows[i]["phase"] != "established":
            i += 1; continue
        j = i
        while j < n and rows[j]["phase"] == "established" and rows[j]["failures"] == 0:
            j += 1
        if j >= n or rows[j]["phase"] != "established":
            i = j; continue                                     # the spell ended without a failure: open, censored
        k = j + 1
        while k < n and rows[k]["phase"] in ("fresh", "banned"):
            k += 1
        if k >= n or rows[k]["phase"] != "established" or k == j + 1:
            i = k; continue                                     # no recovery, or one cut off by the terminal rounds: censored
        spell, rec = rows[i:j + 1], rows[j + 1:k]
        complete.append({"spell": len(spell), "recovery": len(rec), "restarts": sum(1 for r in rec if r["failures"] > 0),
                         "spell_rows": spell, "recovery_rows": rec, "reward": sum(r["profit"] for r in spell + rec)})
        used.update(r["t"] for r in spell + rec); i = k
    return {"complete": complete, "censored_rounds": sum(1 for r in rows if r["t"] not in used)}


def _se(v) -> float:
    v = np.asarray(v, dtype=float)
    return float(v.std(ddof=1) / math.sqrt(len(v))) if len(v) > 1 else float("inf")


def apply_renewal(rows: list, h: float, cfg: dict) -> dict:
    """Separate gates for the recovery formula (3), the renewal identity (4), and the surplus bound (5); estimates from
    complete cycles only. Testable assumptions are checked on every round of their phase; untestable ones are listed as
    assumed. A gate that fails returns applicable_k: false with the failed assumptions named."""
    est = [r for r in rows if r["phase"] == "established"]
    fresh = [r for r in rows if r["phase"] == "fresh" and r.get("generation", 1) > 0]     # the initial window is censored: every original identity is fresh there
    cyc = extract_cycles(rows); comp = cyc["complete"]
    f3, f4, f5 = [], [], []
    if not cfg["reset"]:
        f3.append("replacement after every failure (a waiting plan needs its own recovery accounting)"); f4.append(f3[-1])
    if len(comp) < 2:
        f3.append("at least two complete cycles (finite, estimable cycle rewards and durations)"); f4.append(f3[-1])
    s_vals = [r["S"] for r in est]
    s_mode = max(set(s_vals), key=s_vals.count) if s_vals else 0
    if not s_vals or sum(1 for v in s_vals if v == s_mode) < 0.95 * len(s_vals):
        f4.append("constant service in established rounds")
    fs = [r["S"] for r in fresh]
    if fs and sum(1 for v in fs if v == max(set(fs), key=fs.count)) < 0.95 * len(fs):
        f3.append("constant service in fresh rounds")
    if any(r["K"] != r["S"] for r in fresh):
        f3.append("full fresh auditing"); f4.append("full fresh auditing")
    if not any(r["failures"] > 0 for r in est):
        f4.append("q_E > 0")
    if est and max(r["delta"] for r in est) - min(r["delta"] for r in est) > 1e-9:
        f4.append("a fixed established action")
    gens = {}
    for r in est:
        gens.setdefault("initial" if r.get("generation", 1) == 0 else "replacement", []).append(r)
    if len(gens) == 2 and all(len(v) >= 3 for v in gens.values()):
        rate = {g: sum(x["K"] for x in v) / max(1, sum(x["S"] for x in v)) for g, v in gens.items()}
        if abs(rate["initial"] - rate["replacement"]) > 0.1:
            f4.append("single identity-generation class in established rounds (Lemma 2b: different audit rates)")
    if len(est) >= 8:
        half = len(est) // 2; a, b = est[:half], est[half:]
        qa = [float(x["failures"] > 0) for x in a]; qb = [float(x["failures"] > 0) for x in b]
        ra = [x["profit"] for x in a]; rb = [x["profit"] for x in b]
        if abs(np.mean(qa) - np.mean(qb)) > 2 * math.hypot(_se(qa), _se(qb)) + 1e-12 or abs(np.mean(ra) - np.mean(rb)) > 2 * math.hypot(_se(ra), _se(rb)) + 1e-12:
            f4.append("constant conditional established reward and hazard (the two halves of the established rounds differ)")
    f5 = list(f4)
    rec_rows = [r for c in comp for r in c["recovery_rows"]]
    if any(r["delta"] != 0 for r in rec_rows):
        f5.append("fresh-surplus bound (fresh play is not the honest action, so the in-band optimisation would be needed)")
    if rec_rows:
        fm = float(np.mean([r["profit"] for r in rec_rows]))
        if abs(fm - h) > 2 * _se([r["profit"] for r in rec_rows]) + 1e-12:
            f5.append("common truthful benchmark (honest fresh play does not earn the benchmark rate)")
    out = {"complete_cycles": len(comp), "censored_rounds": cyc["censored_rounds"], "n_established": len(est), "n_fresh": len(fresh),
           "assumed": ["independent cycles", "stationary conditional reward and hazard beyond the two-half diagnostic"],
           "failed_3": f3, "failed_4": f4, "failed_5": f5, "applicable_3": not f3, "applicable_4": not f4, "applicable_5": not f5}
    out["applicable"] = out["applicable_4"]; out["failed_assumptions"] = list(dict.fromkeys(f4 + f3 + f5))
    if comp:
        d = detect(cfg["delta"], cfg["tol"], cfg["sigma"]); d0 = detect(0.0, cfg["tol"], cfg["sigma"])
        est_c = [r for c in comp for r in c["spell_rows"]]
        r_E = float(np.mean([r["profit"] for r in est_c])); q_K = hazard_from_K(est_c, d)
        ED_m = float(np.mean([c["recovery"] for c in comp])); ER_F = float(np.mean([sum(r["profit"] for r in c["recovery_rows"]) for c in comp]))
        per_cycle = [c["reward"] / (c["spell"] + c["recovery"]) for c in comp]
        measured = sum(c["reward"] for c in comp) / sum(c["spell"] + c["recovery"] for c in comp)
        out.update({"r_E": r_E, "q_E_from_K": q_K, "q_E_empirical": len(comp) / len(est_c), "ED_measured": ED_m, "ER_F": ER_F,
                    "ED_formula": expected_recovery((1 - d0) ** s_mode, cfg["L"]) if s_mode else None,
                    "measured_per_round": measured, "measured_se": _se(per_cycle)})
        if out["applicable_4"]:
            out["prediction_4"] = renewal_profit(r_E, q_K, ER_F, ED_m, 0.0, 1.0)
        if out["applicable_5"]:
            out["bound_5"] = surplus_bound(r_E - h, q_K, 0.0, cfg["L"]); out["surplus_measured"] = measured - h
            out["bound_holds"] = bool(measured - h <= out["bound_5"] + 1e-9)
    return out


# ---- the 72 configurations ----------------------------------------------------------------------------------------------

def configurations() -> list[dict]:
    return [{"beta": b, "rule": r, "delta": dl, "reset": rs} for b in (0.02, 0.05, 0.10) for r in ("B2", "B3", "proposed")
            for dl in (0.0, 0.08, 0.16, 0.24) for rs in (True, False)]


def run_all(out: Path) -> dict:
    from sim.calibrate import cell_config, load_calibration
    from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds
    from sim.market import run_episode
    from sim.policies.honest import HonestMax
    from sim.policies.theory_diag import FixedShade
    from sim.positions import positions
    from sim.registry import make_rule
    from scripts.explore_attackers import rule_params
    lk = load_locked(); cal = load_calibration(Path(__file__).resolve().parents[1] / "experiments/calibration.json")
    seeds = [int(s) for s in locked_seeds(lk, "dev_val")[:20]]
    results = []
    tables: dict = {}
    for c in configurations():
        cfg = cell_config(market_config_from_locked(lk), cal, rho=0.2, beta=c["beta"]); f = positions(cfg)["median"]
        RP = rule_params(c["rule"]); per_seed = []
        for sd in seeds:
            pols = [HonestMax() for _ in range(cfg.N)]; pols[f] = FixedShade(c["delta"], c["reset"])
            res = run_episode(cfg, make_rule(c["rule"], RP), pols, sd)
            per_seed.append(round_table(res, cfg, c["rule"], RP, f))
        tables[(c["beta"], c["rule"], c["delta"], c["reset"])] = per_seed
        results.append({**c, "seeds": seeds})
    for r in results:
        key = (r["beta"], r["rule"], r["delta"], r["reset"]); per_seed = tables[key]
        bench = tables[(r["beta"], r["rule"], 0.0, r["reset"])]
        cfg_d = {"reset": r["reset"], "delta": r["delta"], "L": 10, "tol": 0.16, "sigma": 0.05}
        app = []
        for rows, brows in zip(per_seed, bench):
            bmid = [x for x in brows if x["t"] >= W and 200 - x["t"] > 10]
            h = float(np.mean([x["profit"] for x in bmid]))
            a = apply_renewal(rows, h, cfg_d); a["benchmark_h"] = h; app.append(a)
        fh = [finite_horizon(rows, 10) for rows in per_seed]
        r["finite_horizon"] = fh
        r["finite_horizon_per_round"] = [x["per_round"] for x in fh]
        r["renewal"] = app
        r["applicable_seeds"] = sum(1 for a in app if a["applicable_5"])
        r["bound_holds_seeds"] = sum(1 for a in app if a.get("bound_holds"))
        r["established_rates"] = established_rates([x for rows in per_seed for x in rows])
    doc = {"status": "exploratory theorem checks; dev-val seeds 2000 to 2019", "configurations": results}
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(doc, indent=1, default=str) + "\n")
    return doc


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/theory/checks.json")
    a = ap.parse_args(); run_all(Path(a.out))


if __name__ == "__main__":
    main()
