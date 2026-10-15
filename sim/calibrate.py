from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from .cell import market_key
from .config import MarketConfig
from .firstbest import first_best_episode
from .rng import make_draws


@dataclass(frozen=True)
class Calibration:
    S_hat: float
    n_FB: float
    m: float
    market_key: str
    T: int
    seeds: tuple

    def as_dict(self) -> dict:
        d = asdict(self); d["seeds"] = list(self.seeds); return d


def first_best_served(cfg: MarketConfig, values_t: np.ndarray) -> int:
    q_full = np.array([p.q_max for p in cfg.providers]); cost_full = cfg.cost_full
    owner = np.repeat(np.arange(cfg.N), [p.k for p in cfg.providers])
    w = np.maximum(values_t[None, :] * q_full[owner][:, None] - cost_full[owner][:, None], 0.0)
    rows, cols = linear_sum_assignment(w, maximize=True)
    return int((w[rows, cols] > 0).sum())


def calibrate(cfg_base: MarketConfig, seeds) -> Calibration:
    """S_hat and n_FB on the calibration seeds (spec 3). Refuses an invalid market or no seeds."""
    cfg_base.validate()
    seeds = [int(s) for s in seeds]
    if not seeds:
        raise ValueError("calibration needs at least one seed")
    totals, served = [], []
    for s in seeds:
        d = make_draws(cfg_base, s)
        totals.append(first_best_episode(cfg_base, d))
        served.append(sum(first_best_served(cfg_base, d.values[t]) for t in range(cfg_base.T)))
    S_hat = float(np.mean(totals)); n_FB = float(np.mean(served))
    if n_FB <= 0:
        raise ValueError("no job has positive first-best surplus: calibration is undefined for this market")
    return Calibration(S_hat=S_hat, n_FB=n_FB, m=S_hat / n_FB, market_key=market_key(cfg_base), T=int(cfg_base.T), seeds=tuple(seeds))


def cell_config(cfg_base: MarketConfig, cal: Calibration, rho: float, beta: float) -> MarketConfig:
    """alpha = rho * m and B = beta * S_hat for one cell; the calibration must belong to this market."""
    if cal.market_key != market_key(cfg_base):
        raise ValueError("calibration belongs to a different market configuration")
    cfg = MarketConfig(N=cfg_base.N, J=cfg_base.J, T=cfg_base.T, sigma=cfg_base.sigma, e=cfg_base.e, v_min=cfg_base.v_min,
                       v_max=cfg_base.v_max, providers=cfg_base.providers, alpha=float(rho) * cal.m, budget=float(beta) * cal.S_hat)
    cfg.validate()
    return cfg


def save_calibration(cal: Calibration, path: str | Path) -> None:
    Path(path).write_text(json.dumps(cal.as_dict(), indent=2, sort_keys=True) + "\n")


def load_calibration(path: str | Path) -> Calibration:
    d = json.loads(Path(path).read_text())
    return Calibration(S_hat=float(d["S_hat"]), n_FB=float(d["n_FB"]), m=float(d["m"]), market_key=str(d["market_key"]),
                       T=int(d["T"]), seeds=tuple(int(s) for s in d["seeds"]))
