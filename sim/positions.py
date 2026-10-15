from __future__ import annotations

from .config import MarketConfig

ORDER = ("low", "median", "high")


def positions(cfg: MarketConfig) -> dict[str, int]:
    score = [p.b * p.q_max for p in cfg.providers]
    order = sorted(range(cfg.N), key=lambda i: (score[i], i))
    return {"low": order[0], "median": order[cfg.N // 2], "high": order[-1]}


def headline_position(gain_by_position: dict[str, float]) -> str:
    best, best_v = None, None
    for name in ORDER:
        if name in gain_by_position and (best_v is None or gain_by_position[name] > best_v):
            best, best_v = name, gain_by_position[name]
    return best
