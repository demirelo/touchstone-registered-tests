from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import MarketConfig


@dataclass(frozen=True)
class Draws:
    """Every random input of an episode, a pure function of (seed, round)."""
    values: np.ndarray        # (T, J)
    noise: np.ndarray         # (T, N, kmax)
    tie_key: np.ndarray       # (T, J, N) allocation tie-break keys; smaller wins
    audit_u: np.ndarray       # (T,) uniform for the audit count's stochastic rounding
    audit_key: np.ndarray     # (T, J) audit priority per job; smaller audited first
    policy_seed: np.ndarray   # (T, N)


def draws_for_round(cfg: MarketConfig, seed: int, t: int):
    g = np.random.default_rng(np.random.SeedSequence([int(seed), int(t)]))
    values = g.uniform(cfg.v_min, cfg.v_max, size=cfg.J)
    noise = g.normal(0.0, cfg.sigma, size=(cfg.N, cfg.kmax))
    tie_key = g.random(size=(cfg.J, cfg.N))
    audit_u = float(g.random())
    audit_key = g.random(size=cfg.J)
    policy_seed = g.integers(0, 2**31 - 1, size=cfg.N)
    return values, noise, tie_key, audit_u, audit_key, policy_seed


def make_draws(cfg: MarketConfig, seed: int) -> Draws:
    values = np.empty((cfg.T, cfg.J))
    noise = np.empty((cfg.T, cfg.N, cfg.kmax))
    tie_key = np.empty((cfg.T, cfg.J, cfg.N))
    audit_u = np.empty(cfg.T)
    audit_key = np.empty((cfg.T, cfg.J))
    policy_seed = np.empty((cfg.T, cfg.N), dtype=np.int64)
    for t in range(cfg.T):
        v, n, tk, au, ak, ps = draws_for_round(cfg, seed, t)
        values[t], noise[t], tie_key[t], audit_u[t], audit_key[t], policy_seed[t] = v, n, tk, au, ak, ps
    for arr in (values, noise, tie_key, audit_u, audit_key, policy_seed):
        arr.setflags(write=False)
    return Draws(values, noise, tie_key, audit_u, audit_key, policy_seed)
