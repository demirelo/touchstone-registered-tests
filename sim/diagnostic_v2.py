"""Draft-7 evaluation helpers (design 6.2, 6.6, 6.7, 9.3). False-failure refunds: refunds on failed audits in rounds
where the entity's claim did not exceed its delivered effort (a truthful job failed by noise), normalised by S*/N. Served
share: the market's served jobs over the first-best served jobs T min(J, sum k) (every capacity slot has positive
first-best surplus, `MarketConfig.validate`). The fixed-attack decomposition of a gain contrast into its attacker-profit
and reference terms. The training-selected bank envelope. The honest-replacement diagnostic: the focal provider plays
honest-max, replaces its identity once, and plays honest-max after; audited share, profit, and false refunds by age."""
from __future__ import annotations

import numpy as np

from .cell import SeedCache, run_profile
from .policies.base import Action
from .policies.honest import HonestMax

EPS = 1e-12


def _truthful(result) -> np.ndarray:
    c, e = np.asarray(result.claims, dtype=float), np.asarray(result.efforts, dtype=float)
    return np.where(np.isnan(c), False, c <= e + EPS)


def by_entity(result, table, N: int) -> np.ndarray:
    """A (T, identities) ledger table summed to (T, entities) through the episode's identity map."""
    a = np.asarray(table, dtype=float)
    if a.shape[1] == int(N) and not hasattr(result, "entity_of"):
        return a
    out = np.zeros((a.shape[0], int(N)))
    for ident, e in enumerate(result.entity_of):
        out[:, int(e)] += a[:, ident]
    return out


def false_refunds(result, focal: int, N: int) -> tuple[float, float]:
    """(focal, all other entities) refunds on failed truthful jobs, each normalised by S*/N."""
    mask = (np.asarray(result.failures) > 0) & _truthful(result)
    ref = np.where(mask, by_entity(result, result.ledger.refunds, N), 0.0); scale = float(result.sstar) / int(N)
    return float(ref[:, int(focal)].sum()) / scale, float(ref.sum() - ref[:, int(focal)].sum()) / scale


def served_share(result, cfg) -> float:
    n_fb = int(cfg.T) * min(int(cfg.J), sum(int(p.k) for p in cfg.providers))
    return float(np.asarray(result.served).sum()) / n_fb


def extras(attack_results, ref_results, cfg, focal: int) -> dict:
    """The draft-7 evaluation fields per seed (design 9.3 Q1 side fields)."""
    out = {"served_share_attack": [], "served_share_ref": [], "false_refund_focal_attack": [], "false_refund_others_attack": [],
           "false_refund_focal_ref": [], "false_refund_others_ref": []}
    for tag, res in (("attack", attack_results), ("ref", ref_results)):
        for r in res:
            f, o = false_refunds(r, focal, cfg.N)
            out[f"served_share_{tag}"].append(served_share(r, cfg))
            out[f"false_refund_focal_{tag}"].append(f); out[f"false_refund_others_{tag}"].append(o)
    return out


def decompose(row: dict, rule_r: str, rule_c: str) -> dict:
    """gain_R - gain_C = attack_term - reference_term per seed (design 6.6), from normalised per-seed profits."""
    a = np.subtract(row[rule_r]["profit_attack"], row[rule_c]["profit_attack"])
    r = np.subtract(row[rule_r]["profit_ref"], row[rule_c]["profit_ref"])
    return {"attack_term": a.tolist(), "reference_term": r.tolist()}


def envelope_rule(train: dict, rule: str) -> str:
    """The bank attack with the highest training gain against `rule` (design 6.6), ties by bank order."""
    k = list(train["rules"]).index(rule); best = None
    for i, a in enumerate(train["attacks"]):
        g = float(train["matrix"][i][k])
        if best is None or g > best[1]:
            best = (a, g)
    return best[0]


class _HonestReplacer:
    name = "honest_replacer"

    def __init__(self, at: int) -> None:
        self.at = int(at)

    def act(self, view) -> Action:
        a = HonestMax().act(view)
        return Action(effort=a.effort, offer=a.offer, exit=int(view.t) == self.at)


def honest_replacement(cfg, rule_factory, focal: int, seeds, cache: SeedCache, replace_at: int = 50, bin_width: int = 10) -> dict:
    """Design 6.7: per age bin of the replacement identity, the audited share of the focal provider's served jobs, its profit
    per round, and its false-failure refunds (normalised by S*/N); every other provider plays honest-max."""
    fs = [HonestMax for _ in range(cfg.N)]; fs[int(focal)] = lambda: _HonestReplacer(replace_at)
    res = run_profile(cfg, rule_factory, fs, seeds, cache)
    T = int(cfg.T); edges = list(range(int(replace_at), T, int(bin_width))); bins = []
    for lo in edges:
        hi = min(lo + int(bin_width), T); rows = slice(lo, hi)
        served = sum(int(np.asarray(r.served)[rows, focal].sum()) for r in res)
        audited = sum(sum(1 for rec in r.history[lo:hi] for au in rec.audits if r.entity_of[au.provider] == int(focal)) for r in res)
        profit = [float((by_entity(r, r.ledger.funding, cfg.N) - by_entity(r, r.ledger.cost, cfg.N))[rows, focal].sum()) / (r.sstar / cfg.N) for r in res]
        mask = [(np.asarray(r.failures)[rows, focal] > 0) & _truthful(r)[rows, focal] for r in res]
        fr = [float(np.where(m, by_entity(r, r.ledger.refunds, cfg.N)[rows, focal], 0.0).sum()) / (r.sstar / cfg.N) for m, r in zip(mask, res)]
        bins.append({"age": [lo - int(replace_at), hi - int(replace_at)], "audited_share": audited / served if served else 0.0,
                     "profit_per_round": float(np.mean(profit)) / (hi - lo), "false_refund": float(np.mean(fr))})
    return {"replace_at": int(replace_at), "bin_width": int(bin_width), "seeds": [int(s) for s in seeds], "bins": bins}
