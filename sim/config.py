from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ProviderParams:
    q_max: float
    a: float
    b: float
    k: int


@dataclass(frozen=True)
class MarketConfig:
    N: int
    J: int
    T: int
    sigma: float
    e: float
    v_min: float
    v_max: float
    providers: tuple[ProviderParams, ...]
    alpha: float
    budget: float

    @property
    def kmax(self) -> int:
        return max(p.k for p in self.providers)

    @property
    def q90(self) -> float:
        return self.v_min + 0.9 * (self.v_max - self.v_min)

    @property
    def cost_full(self) -> np.ndarray:
        return np.array([p.a + p.b * p.q_max for p in self.providers])

    def validate(self) -> None:
        if len(self.providers) != self.N:
            raise ValueError("providers length must equal N")
        if self.J < 1 or self.T < 1:
            raise ValueError("J and T must be positive")
        if not (0.0 < self.v_min <= self.v_max):
            raise ValueError("need 0 < v_min <= v_max")
        if self.sigma < 0 or self.alpha < 0 or self.budget < 0 or self.e < 0:
            raise ValueError("sigma, alpha, budget, e must be non-negative")
        for i, p in enumerate(self.providers):
            if not (0.0 < p.q_max <= 1.0):
                raise ValueError(f"provider {i}: q_max must be in (0, 1]")
            if p.a < 0 or p.b <= 0:
                raise ValueError(f"provider {i}: need a >= 0 and b > 0")
            if p.k < 1:
                raise ValueError(f"provider {i}: capacity k must be >= 1")
            weight = self.v_min * p.q_max - p.a - p.b * p.q_max
            if weight <= 0:
                raise ValueError(f"provider {i}: first-best weight at v_min is {weight:.4f}, must be > 0")
        p_top = 0.9 * self.q90
        c_min = float(self.cost_full.min())
        if not (p_top > c_min):
            raise ValueError(f"price grid condition fails: 0.9*q90={p_top:.4f} <= c_min={c_min:.4f}")

    @classmethod
    def default(cls) -> "MarketConfig":
        q_max = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.00]
        b = [0.40, 0.38, 0.36, 0.34, 0.32, 0.30, 0.28, 0.26, 0.24, 0.22]
        providers = tuple(ProviderParams(q_max=q, a=0.02, b=bb, k=6) for q, bb in zip(q_max, b))
        return cls(N=10, J=50, T=200, sigma=0.05, e=0.0, v_min=0.6, v_max=1.4,
                   providers=providers, alpha=0.05, budget=0.0)
