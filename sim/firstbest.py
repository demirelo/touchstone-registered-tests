from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from .config import MarketConfig
from .rng import Draws


def first_best_round(cfg: MarketConfig, values_t: np.ndarray) -> float:
    """Exact maximum-weight assignment of unit jobs to capacity slots at full
    effort; weight max(0, v_j q_max_i - a_i - b_i q_max_i); zero weight = do not serve."""
    q_full = np.array([p.q_max for p in cfg.providers])
    cost_full = cfg.cost_full
    owner = np.repeat(np.arange(cfg.N), [p.k for p in cfg.providers])
    w = np.maximum(values_t[None, :] * q_full[owner][:, None] - cost_full[owner][:, None], 0.0)
    rows, cols = linear_sum_assignment(w, maximize=True)
    return float(w[rows, cols].sum())


def first_best_episode(cfg: MarketConfig, draws: Draws) -> float:
    return float(sum(first_best_round(cfg, draws.values[t]) for t in range(cfg.T)))
