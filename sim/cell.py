from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .config import MarketConfig
from .firstbest import first_best_episode
from .market import EpisodeResult, run_episode
from .policies.base import Action, ProviderView
from .policies.honest import HonestMax
from .rng import Draws, make_draws


def market_key(cfg: MarketConfig) -> str:
    """Hash of the market primitives; alpha and budget excluded (draws and S* do not depend on them)."""
    parts = (cfg.N, cfg.J, cfg.T, cfg.sigma, cfg.e, cfg.v_min, cfg.v_max,
             tuple((p.q_max, p.a, p.b, p.k) for p in cfg.providers))
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


class SeedCache:
    """Draws and S* per (market, seed): computed once, shared by every cell. Counts episodes run."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, int], tuple[Draws, float]] = {}
        self.hits = 0
        self.misses = 0
        self.runs = 0

    def get(self, cfg: MarketConfig, seed: int) -> tuple[Draws, float]:
        key = (market_key(cfg), int(seed))
        if key in self._store:
            self.hits += 1
            return self._store[key]
        self.misses += 1
        d = make_draws(cfg, seed)
        self._store[key] = (d, first_best_episode(cfg, d))
        return self._store[key]


class Abstain:
    name = "abstain"

    def act(self, view: ProviderView) -> Action:
        return Action(effort=0.0, offer=None)


@dataclass(frozen=True)
class Cell:
    cfg: MarketConfig
    rule_factory: Callable
    focal: int
    seeds: tuple[int, ...]
    name: str
    others: tuple = ()      # ((entity, policy_factory), ...) for non-focal entities not on honest-max


@dataclass
class FocalRun:
    profit: np.ndarray
    normalized: np.ndarray
    inflated_per_seed: np.ndarray
    inflated: bool
    results: list = field(default_factory=list)


def run_profile(cfg: MarketConfig, rule_factory: Callable, factories: list, seeds, cache: SeedCache) -> list[EpisodeResult]:
    out = []
    for seed in seeds:
        d, sstar = cache.get(cfg, seed)
        pols = [f() for f in factories]
        out.append(run_episode(cfg, rule_factory(), pols, int(seed), draws=d, sstar=sstar))
        cache.runs += 1
    return out


def run_focal(cell: Cell, policy_factory: Callable, cache: SeedCache) -> FocalRun:
    factories: list = [HonestMax for _ in range(cell.cfg.N)]
    for e, f in cell.others:
        factories[e] = f
    factories[cell.focal] = policy_factory
    results = run_profile(cell.cfg, cell.rule_factory, factories, cell.seeds, cache)
    profits = np.array([float(r.profit[cell.focal]) for r in results])
    norms = np.array([float(r.profit[cell.focal] / (r.sstar / cell.cfg.N)) for r in results])
    infl = np.array([bool(np.any(r.claims[:, cell.focal] > r.efforts[:, cell.focal])) for r in results])   # nan claims (no offer) compare False
    return FocalRun(profit=profits, normalized=norms, inflated_per_seed=infl, inflated=bool(infl.any()), results=results)
