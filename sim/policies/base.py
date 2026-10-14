from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import cached_property
from typing import Protocol

import numpy as np

from ..config import ProviderParams
from ..mechanisms.base import Offer


@dataclass
class ProviderHistory:
    served: list[int] = field(default_factory=list)
    payment: list[float] = field(default_factory=list)
    audited: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)
    refunded: list[float] = field(default_factory=list)
    banned_until: list[int] = field(default_factory=list)

    def append(self, served: int, payment: float, audited: int, failed: int, refunded: float, banned_until: int) -> None:
        self.served.append(served); self.payment.append(payment); self.audited.append(audited)
        self.failed.append(failed); self.refunded.append(refunded); self.banned_until.append(banned_until)


@dataclass(frozen=True)
class ProviderView:
    i: int
    params: ProviderParams
    t: int
    posted_prices: tuple[float, ...] | None
    history: ProviderHistory
    policy_seed: int

    @cached_property
    def rng(self) -> np.random.Generator:
        return np.random.default_rng(int(self.policy_seed))


@dataclass(frozen=True)
class Action:
    effort: float
    offer: Offer | None
    exit: bool = False


def validate_action(action: Action, params: ProviderParams) -> None:
    if action.exit:
        raise NotImplementedError("exit and re-entry arrive with identity replacement in plan 2")
    e = action.effort
    if not (isinstance(e, (int, float, np.floating)) and math.isfinite(float(e))):
        raise ValueError("effort must be finite")
    if not (0.0 <= float(e) <= params.q_max + 1e-12):
        raise ValueError(f"effort {e} outside [0, q_max={params.q_max}]")


class Policy(Protocol):
    name: str

    def act(self, view: ProviderView) -> Action: ...
