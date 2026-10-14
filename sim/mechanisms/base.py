from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

L_MAX = 50   # longest admissible ban, rounds (spec 4.0)
H_MAX = 3    # outstanding bond at most this many rounds of net released receipts (spec 4.0)


@dataclass(frozen=True)
class Offer:
    """Public offer. Effort is private and never part of it."""
    claim: float
    bid: float

    def __post_init__(self) -> None:
        if not (isinstance(self.claim, (int, float)) and math.isfinite(self.claim) and 0.0 <= self.claim <= 1.0):
            raise ValueError("claim must be a finite number in [0, 1]")
        if not (isinstance(self.bid, (int, float)) and math.isfinite(self.bid) and self.bid >= 0.0):
            raise ValueError("bid must be a finite non-negative number")


Offers = dict[int, Offer]


@dataclass(frozen=True)
class AuditRecord:
    job: int
    provider: int
    delivered: float
    claim: float
    failed: bool


@dataclass
class Consequences:
    refunds: dict[int, float] = field(default_factory=dict)     # job -> amount
    bans: dict[int, int] = field(default_factory=dict)          # identity -> rounds
    holdbacks: dict[int, float] = field(default_factory=dict)   # identity -> amount into bond
    forfeits: dict[int, float] = field(default_factory=dict)    # identity -> amount from bond to buyers
    releases: dict[int, float] = field(default_factory=dict)    # identity -> amount from bond to provider


@dataclass(frozen=True)
class RoundRecord:
    t: int
    offers: Offers
    assignment: dict[int, int]
    payments: dict[int, float]
    audits: tuple[AuditRecord, ...]
    consequences: Consequences


def _ro(a: np.ndarray) -> np.ndarray:
    b = np.array(a, copy=True)
    b.setflags(write=False)
    return b


@dataclass(frozen=True)
class StateView:
    """What a rule may see. Arrays are read-only copies; `memory` is the rule's own."""
    t: int
    T: int
    N: int
    audits_left: int
    audit_u: float
    audit_key: np.ndarray
    banned_until: np.ndarray
    bond: np.ndarray
    capacity: np.ndarray
    escrow: Mapping[int, float]
    history: tuple[RoundRecord, ...]
    memory: dict

    def __post_init__(self) -> None:
        object.__setattr__(self, "audit_key", _ro(self.audit_key))
        object.__setattr__(self, "banned_until", _ro(self.banned_until))
        object.__setattr__(self, "bond", _ro(self.bond))
        object.__setattr__(self, "capacity", _ro(self.capacity))
        object.__setattr__(self, "escrow", dict(self.escrow))

    def is_active(self, i: int) -> bool:
        return self.t >= int(self.banned_until[i])


class Mechanism(ABC):
    name: str = "mechanism"
    tol: float | None = None   # declared audit tolerance; None if the rule never audits

    def bind(self, cfg) -> None:
        """Receive the constants a rule may know (B, alpha, T, N). Default: nothing."""

    @abstractmethod
    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]: ...

    @abstractmethod
    def price(self, assignment: dict[int, int], values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, float]: ...

    @abstractmethod
    def audit(self, assignment: dict[int, int], view: StateView) -> list[int]: ...

    @abstractmethod
    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences: ...

    @abstractmethod
    def describe(self) -> dict[str, str]: ...
