# Touchstone core engine implementation plan (plan 1 of 3), version 2

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the claimed-quality market simulator with a harness that enforces the admissible rule class, a ledger that owns every money flow including bonds, action-independent operator randomness, the exact first-best benchmark, baselines B1 to B3, honest-max and fixed-cheat policies with the truthful twin, core metrics, and a timed pilot that runs one 200-round B2 episode in under 45 ms.

**Architecture:** A Python package `sim` with NumPy for per-round vector work. All randomness (job values, delivery noise, allocation tie-breaks, audit rounding, audit selection, policy seeds) is precomputed per seed and keyed by round, so no action changes any draw. A `Mechanism` receives a read-only `StateView` and public offers and returns an assignment, payments, an audit list, and `Consequences`; the harness validates every one of those outputs against the spec's admissible class before the `Ledger` applies them. The harness records audit outcomes itself with the rule's declared tolerance. Policies see their own view only.

**Tech Stack:** Python 3.13, numpy, scipy (`linear_sum_assignment`, `stats`), pytest. Package and dependency management with `uv`.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5). This plan implements sections 3, 4 (interface, admissible class, B1 to B3), 5.1, 5.2 (honest-max and the twin wrapper), 5.3 (D1 only), 7 (S*, ledger, W, efficiency, gain, harm), 12 (the tests those sections name), and the first gate of section 13. Plan 2 (search, D2, manifest, calibration, tuning, coverage study, `check_claim.py`, LLM and Jev actors, `describe()` rendering, H3 identity replacement) and plan 3 (post-freeze evaluation) follow.

**Version 2 changes:** rewritten after two independent reviews (Astra, Opus) that executed version 1's code. Headline changes: a read-only state view, harness-side validation of every rule output, audit records with a failure flag, bond forfeits and releases in the ledger now, integer audit allowances, precomputed operator randomness, S* computed once per seed, and a benchmark at a realistic audit budget.

**Scope split, stated once:** Plan 1 stops at the pilot gate of 2026-10-17. It does not contain CMA-ES, D2, the candidate bank, the coverage study, `describe()` rendering to prose, identity replacement, or any proposed rule. The admissible class, including bond hold-backs, forfeits, and releases, is complete in plan 1 because the lock freezes it.

## Global Constraints

- Jobs are unit jobs: every job has size 1 (spec 3).
- Delivered quality is `effort + eps`, `eps ~ N(0, sigma^2)`, never clipped (spec 3).
- A claim is truthful iff `claim <= effort` (spec 3).
- A rule may read only: current offers (claim and bid), current job values, audit records it bought, the public history, its own memory, and the config constants; never effort, unaudited delivery, or future draws (spec 3, 4.0).
- Admissible consequences only: refund up to the escrowed payment of an audited job that failed; ban an identity with a failed audit this round for at most `L_MAX = 50` rounds; hold back receipts as a bond with the outstanding bond at most the last `H_MAX = 3` rounds of net released receipts; forfeit at most the bond and at most the escrow of that identity's failed jobs, booked once to those jobs' buyers; release any part of the bond. No fees, no consequence for an unaudited job (spec 4.0).
- The operator injects no money; its net position is audit cost only; outstanding bonds are released at the end of the episode (spec 4.0, 7).
- Audit purchases are integers; the total never exceeds `floor(B / alpha)` in any seed (spec 3, 4.1).
- Every draw is a pure function of `(seed, round)` with a fixed intra-round layout; no action changes any draw (spec 7, keying recorded in Task 12).
- `S*` is computed once per seed and shared across cells (spec 7).
- Same config and seed give a byte-identical CSV (spec 12).
- Cash conservation holds after every round (spec 7).
- Pilot gate: one `T = 200` B2 episode at `B = 0.05 S_hat` under 45 ms on one core (spec 13).
- Package `sim/`, typed state in `sim/mechanisms/base.py`, tests under `tests/`, scripts under `scripts/` (spec 11, 6).
- Validity: for every provider `v_min q_max_i - a_i - b_i q_max_i > 0`, and `0.9 q90(v) > min_i (a_i + b_i q_max_i)` (spec 3).

## Review Focus

1. Every provider banned in some round: every job stays unserved, `W` and efficiency still compute, nothing raises. Task 8.
2. Remaining allowance below one audit: zero audits that round, no negative budget, no division by zero in the last round. Task 8.
3. A provider whose capacity exceeds the number of jobs: `S*` slot matrix and allocation handle it. Tasks 3 and 7.
4. Two jobs with identical values: stable descending sort, same seed gives the same assignment. Task 7.
5. Negative delivered quality from noise: buyer value negative for that job, failure test `y < claim - tol` still applies, nothing clips. Task 8.
6. A rule that returns an invalid output (assignment to an abstainer, payment above acceptance, duplicate audit, refund on an unaudited job, ban without a failed audit, hold-back above the cap, forfeit above the bond): the harness raises before any money moves. Tasks 6, 7, 10.

---

### Task 1: Package scaffold and test harness

**Files:**
- Create: `pyproject.toml`, `sim/__init__.py`, `tests/__init__.py`, `tests/test_scaffold.py`
- Modify: `.gitignore` (append `.venv/`, `*.egg-info/`, `.pytest_cache/`)

**Interfaces:**
- Produces: importable package `sim` with `__version__ = "0.1.0"`; `uv run pytest` works.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scaffold.py
def test_package_imports():
    import sim
    assert sim.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest tests/test_scaffold.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim'`

- [ ] **Step 3: Write the scaffold**

```toml
# pyproject.toml
[project]
name = "touchstone"
version = "0.1.0"
description = "Audit-and-allocation rules for markets of adaptive agents: simulator"
requires-python = ">=3.12"
dependencies = ["numpy>=2.0", "scipy>=1.13"]

[dependency-groups]
dev = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["sim"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
# sim/__init__.py
__version__ = "0.1.0"
```

```python
# tests/__init__.py
```

Append to `.gitignore`: `.venv/`, `*.egg-info/`, `.pytest_cache/`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv sync && uv run pytest tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock sim/__init__.py tests/__init__.py tests/test_scaffold.py .gitignore
git commit -m "feat: package scaffold and test harness"
```

---

### Task 2: Configuration with both validity conditions, and round-keyed draws

**Files:**
- Create: `sim/config.py`, `sim/rng.py`
- Test: `tests/test_config.py`, `tests/test_rng.py`

**Interfaces:**
- Produces:
  - `ProviderParams(q_max, a, b, k)` frozen dataclass.
  - `MarketConfig(N, J, T, sigma, e, v_min, v_max, providers, alpha, budget)` frozen dataclass; `validate()`; `kmax`; `q90`; `cost_full: np.ndarray`; `classmethod default()`.
  - `Draws(values[T,J], noise[T,N,kmax], tie_key[T,J,N], audit_u[T], audit_key[T,J], policy_seed[T,N])`, arrays read-only.
  - `draws_for_round(cfg, seed, t) -> tuple`, `make_draws(cfg, seed) -> Draws`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import pytest
from sim.config import MarketConfig, ProviderParams


def with_last_provider(base, p):
    return MarketConfig(N=base.N, J=base.J, T=base.T, sigma=base.sigma, e=base.e,
                        v_min=base.v_min, v_max=base.v_max,
                        providers=base.providers[:-1] + (p,), alpha=base.alpha, budget=base.budget)


def test_default_config_is_valid():
    cfg = MarketConfig.default()
    cfg.validate()
    assert cfg.N == 10 and cfg.J == 50 and cfg.T == 200
    assert len(cfg.providers) == cfg.N


def test_validity_rejects_unprofitable_provider():
    cfg = with_last_provider(MarketConfig.default(), ProviderParams(q_max=0.5, a=0.5, b=0.5, k=5))
    with pytest.raises(ValueError, match="first-best weight"):
        cfg.validate()


def test_validity_rejects_zero_capacity():
    cfg = with_last_provider(MarketConfig.default(), ProviderParams(q_max=0.9, a=0.02, b=0.3, k=0))
    with pytest.raises(ValueError, match="capacity"):
        cfg.validate()


def test_validity_rejects_price_grid_condition():
    # constant value 1, q_max 1, a 0.94, b 0.01: first-best weight 0.05 > 0 but
    # P_top = 0.9 * q90 = 0.9 < c_min = 0.95
    cfg = MarketConfig(N=1, J=5, T=2, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0,
                       providers=(ProviderParams(q_max=1.0, a=0.94, b=0.01, k=5),),
                       alpha=0.05, budget=0.0)
    with pytest.raises(ValueError, match="price grid"):
        cfg.validate()


def test_validity_price_grid_boundary_is_strict():
    cfg = MarketConfig(N=1, J=5, T=2, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0,
                       providers=(ProviderParams(q_max=1.0, a=0.89, b=0.01, k=5),),
                       alpha=0.05, budget=0.0)
    with pytest.raises(ValueError, match="price grid"):
        cfg.validate()
```

```python
# tests/test_rng.py
import numpy as np
from sim.config import MarketConfig
from sim.rng import make_draws, draws_for_round


def test_draw_shapes_and_ranges():
    cfg = MarketConfig.default()
    d = make_draws(cfg, seed=7)
    assert d.values.shape == (cfg.T, cfg.J)
    assert d.noise.shape == (cfg.T, cfg.N, cfg.kmax)
    assert d.tie_key.shape == (cfg.T, cfg.J, cfg.N)
    assert d.audit_u.shape == (cfg.T,)
    assert d.audit_key.shape == (cfg.T, cfg.J)
    assert d.policy_seed.shape == (cfg.T, cfg.N)
    assert d.values.min() >= cfg.v_min and d.values.max() <= cfg.v_max
    assert abs(d.noise.std() - cfg.sigma) < 0.01
    assert 0.0 <= d.audit_u.min() and d.audit_u.max() < 1.0


def test_same_seed_same_draws_and_different_seed_differs():
    cfg = MarketConfig.default()
    a, b, c = make_draws(cfg, 3), make_draws(cfg, 3), make_draws(cfg, 4)
    for name in ("values", "noise", "tie_key", "audit_u", "audit_key", "policy_seed"):
        assert np.array_equal(getattr(a, name), getattr(b, name))
    assert not np.array_equal(a.values, c.values)


def test_round_draws_are_pure_function_of_seed_and_round():
    cfg = MarketConfig.default()
    full = make_draws(cfg, seed=11)
    for t in (0, 1, 57, cfg.T - 1):
        v, n, tk, au, ak, ps = draws_for_round(cfg, seed=11, t=t)
        assert np.array_equal(v, full.values[t])
        assert np.array_equal(n, full.noise[t])
        assert np.array_equal(tk, full.tie_key[t])
        assert au == full.audit_u[t]
        assert np.array_equal(ak, full.audit_key[t])
        assert np.array_equal(ps, full.policy_seed[t])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py tests/test_rng.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.config'`

- [ ] **Step 3: Write the implementation**

```python
# sim/config.py
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
```

```python
# sim/rng.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py tests/test_rng.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/config.py sim/rng.py tests/test_config.py tests/test_rng.py
git commit -m "feat: config with both validity conditions; round-keyed action-independent draws"
```

---

### Task 3: First-best benchmark S*

**Files:**
- Create: `sim/firstbest.py`
- Test: `tests/test_firstbest.py`

**Interfaces:**
- Produces: `first_best_round(cfg, values_t) -> float`; `first_best_episode(cfg, draws) -> float`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_firstbest.py
import numpy as np
import pytest
from sim.config import MarketConfig, ProviderParams
from sim.firstbest import first_best_round, first_best_episode
from sim.rng import make_draws


def one_provider(q_max=0.8, a=0.1, b=0.5, k=1, J=1, v=1.0):
    return MarketConfig(N=1, J=J, T=1, sigma=0.0, e=0.0, v_min=v, v_max=v,
                        providers=(ProviderParams(q_max=q_max, a=a, b=b, k=k),), alpha=0.0, budget=0.0)


def test_one_provider_one_job_closed_form():
    assert first_best_round(one_provider(), np.array([1.0])) == pytest.approx(0.3)


def test_capacity_exceeds_jobs():
    assert first_best_round(one_provider(k=7, J=2), np.array([1.0, 1.0])) == pytest.approx(0.6)


def test_jobs_exceed_capacity_picks_highest_values():
    cfg = MarketConfig(N=1, J=3, T=1, sigma=0.0, e=0.0, v_min=0.6, v_max=2.0,
                       providers=(ProviderParams(q_max=1.0, a=0.0, b=0.5, k=2),), alpha=0.0, budget=0.0)
    assert first_best_round(cfg, np.array([2.0, 1.0, 0.6])) == pytest.approx(2.0)


def test_episode_sums_rounds_and_is_positive():
    cfg = MarketConfig.default()
    d = make_draws(cfg, seed=1)
    total = first_best_episode(cfg, d)
    assert total == pytest.approx(sum(first_best_round(cfg, d.values[t]) for t in range(cfg.T)))
    assert total > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_firstbest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.firstbest'`

- [ ] **Step 3: Write the implementation**

```python
# sim/firstbest.py
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from .config import MarketConfig
from .rng import Draws


def first_best_round(cfg: MarketConfig, values_t: np.ndarray) -> float:
    q_full = np.array([p.q_max for p in cfg.providers])
    cost_full = cfg.cost_full
    owner = np.repeat(np.arange(cfg.N), [p.k for p in cfg.providers])
    w = np.maximum(values_t[None, :] * q_full[owner][:, None] - cost_full[owner][:, None], 0.0)
    rows, cols = linear_sum_assignment(w, maximize=True)
    return float(w[rows, cols].sum())


def first_best_episode(cfg: MarketConfig, draws: Draws) -> float:
    return float(sum(first_best_round(cfg, draws.values[t]) for t in range(cfg.T)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_firstbest.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/firstbest.py tests/test_firstbest.py
git commit -m "feat: exact first-best benchmark"
```

---

### Task 4: Typed state, offers, audit records, consequences, and the mechanism interface

**Files:**
- Create: `sim/mechanisms/__init__.py`, `sim/mechanisms/base.py`
- Test: `tests/test_base_types.py`

**Interfaces:**
- Produces (all in `sim/mechanisms/base.py`):
  - `L_MAX = 50`, `H_MAX = 3`.
  - `Offer(claim, bid)` frozen; `ValueError` outside `[0, 1]` claim, negative or non-finite bid, non-finite claim. `Offers = dict[int, Offer]`.
  - `AuditRecord(job, provider, delivered, claim, failed)` frozen.
  - `Consequences(refunds, bans, holdbacks, forfeits, releases)` dataclass of dicts.
  - `RoundRecord(t, offers, assignment, payments, audits, consequences)` frozen.
  - `StateView(t, T, N, audits_left, audit_u, audit_key, banned_until, bond, capacity, escrow, history, memory)`; arrays are read-only copies; `memory` is the rule's own mutable dict; `is_active(i)`.
  - `Mechanism` ABC: `name`, `tol`, `bind(cfg)` (default no-op), `allocate(values_t, offers, view)`, `price(assignment, values_t, offers, view)`, `audit(assignment, view)`, `enforce(records, view)`, `describe()`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_base_types.py
import numpy as np
import pytest
from sim.mechanisms.base import Offer, StateView, Consequences, AuditRecord, L_MAX, H_MAX


def test_offer_rejects_effort_and_bad_ranges():
    with pytest.raises(TypeError):
        Offer(claim=0.8, bid=0.3, effort=0.7)  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        Offer(claim=1.2, bid=0.3)
    with pytest.raises(ValueError):
        Offer(claim=0.5, bid=-0.1)
    with pytest.raises(ValueError):
        Offer(claim=float("nan"), bid=0.0)


def mkview(t=0, banned=(0, 0), caps=(1, 1)):
    return StateView(t=t, T=5, N=2, audits_left=0, audit_u=0.5, audit_key=np.zeros(1),
                     banned_until=np.array(banned, dtype=np.int64), bond=np.zeros(2),
                     capacity=np.array(caps), escrow={}, history=(), memory={})


def test_state_view_arrays_are_read_only():
    v = mkview()
    with pytest.raises(ValueError):
        v.banned_until[0] = 9
    with pytest.raises(ValueError):
        v.bond[0] = 1.0
    with pytest.raises(ValueError):
        v.capacity[0] = 0
    v.memory["x"] = 1


def test_state_view_is_active():
    assert not mkview(t=3, banned=(4, 0)).is_active(0)
    assert mkview(t=4, banned=(4, 0)).is_active(0)


def test_constants_and_defaults():
    assert L_MAX == 50 and H_MAX == 3
    c = Consequences()
    assert c.refunds == {} and c.bans == {} and c.holdbacks == {} and c.forfeits == {} and c.releases == {}
    assert AuditRecord(job=1, provider=2, delivered=0.7, claim=0.9, failed=True).failed
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_base_types.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.mechanisms'`

- [ ] **Step 3: Write the implementation**

```python
# sim/mechanisms/__init__.py
```

```python
# sim/mechanisms/base.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_base_types.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/mechanisms/__init__.py sim/mechanisms/base.py tests/test_base_types.py
git commit -m "feat: typed read-only state view, offers, audit records, consequences, mechanism interface"
```

---

### Task 5: Ledger with per-round accounting, bonds, forfeits, releases, and conservation

**Files:**
- Create: `sim/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Produces: `Ledger(N, T)` with `(T, N)` arrays `funding, refunds, released, holdback_in, holdback_out, forfeits, cost, entry`, `audit_cost[T]`, `bond[N]`; methods `fund(t, job, provider, amount, escrow, owner)`, `charge_cost(t, provider, amount)`, `charge_entry(t, provider, amount)`, `charge_audit(t, amount)`, `recent_receipts() -> np.ndarray[N]`, `settle(t, escrow, owner, cons, failed_jobs_of)`, `terminal_settlement()`, `profit() -> np.ndarray[N]`, `buyer_credit() -> float`, `check_conservation(escrow_outstanding)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ledger.py
import numpy as np
import pytest
from sim.ledger import Ledger
from sim.mechanisms.base import Consequences


def test_fund_settle_releases():
    led = Ledger(N=2, T=3)
    esc, own = {}, {}
    led.fund(0, job=0, provider=1, amount=0.7, escrow=esc, owner=own)
    led.settle(0, esc, own, Consequences(), failed_jobs_of={})
    assert led.released[0, 1] == pytest.approx(0.7)
    assert led.profit()[1] == pytest.approx(0.7)
    led.check_conservation(escrow_outstanding=0.0)


def test_refund_reduces_release_and_credits_buyer():
    led = Ledger(N=1, T=2)
    esc, own = {}, {}
    led.fund(0, 0, 0, 1.0, esc, own)
    led.settle(0, esc, own, Consequences(refunds={0: 1.0}), failed_jobs_of={0: [0]})
    assert led.refunds[0, 0] == pytest.approx(1.0) and led.released[0, 0] == pytest.approx(0.0)
    assert led.buyer_credit() == pytest.approx(1.0)
    led.check_conservation(0.0)


def test_holdback_then_forfeit_and_release_single_booking():
    led = Ledger(N=1, T=4)
    esc, own = {}, {}
    led.fund(0, 0, 0, 1.0, esc, own); led.settle(0, esc, own, Consequences(), {})
    led.fund(1, 1, 0, 1.0, esc, own)
    led.settle(1, esc, own, Consequences(holdbacks={0: 0.4}), {})
    assert led.bond[0] == pytest.approx(0.4)
    assert led.released[1, 0] == pytest.approx(0.6)
    led.fund(2, 2, 0, 1.0, esc, own)
    led.settle(2, esc, own, Consequences(refunds={2: 1.0}, forfeits={0: 0.3}, releases={0: 0.05}),
               failed_jobs_of={0: [2]})
    assert led.bond[0] == pytest.approx(0.05)
    assert led.forfeits[2, 0] == pytest.approx(0.3)
    assert led.holdback_out[2, 0] == pytest.approx(0.05)
    assert led.buyer_credit() == pytest.approx(1.3)
    led.check_conservation(0.0)
    led.terminal_settlement()
    assert led.bond[0] == pytest.approx(0.0)
    assert led.profit()[0] == pytest.approx(1.0 + 0.6 + 0.0 + 0.05 + 0.05)
    led.check_conservation(0.0)


def test_forced_release_when_cap_shrinks():
    led = Ledger(N=1, T=8)
    esc, own = {}, {}
    for t in range(8):
        led.fund(t, t, 0, 1.0, esc, own)
        led.settle(t, esc, own, Consequences(holdbacks={0: 0.5}) if t > 0 else Consequences(), {})
        assert led.bond[0] <= led.recent_receipts()[0] + 1e-9
        led.check_conservation(0.0)
    assert led.bond[0] == pytest.approx(1.5)


def test_conservation_rejects_nan():
    led = Ledger(N=1, T=1)
    esc, own = {}, {}
    led.fund(0, 0, 0, 1.0, esc, own)
    led.released[0, 0] = float("nan")
    with pytest.raises(AssertionError):
        led.check_conservation(0.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.ledger'`

- [ ] **Step 3: Write the implementation**

```python
# sim/ledger.py
from __future__ import annotations

import numpy as np

from .mechanisms.base import Consequences, H_MAX


class Ledger:
    """Owns every money flow. Conservation after every settlement:
    funding = released + refunds + holdback_out + forfeits + bond + escrow."""

    def __init__(self, N: int, T: int) -> None:
        self.N, self.T = N, T
        self.funding = np.zeros((T, N)); self.refunds = np.zeros((T, N)); self.released = np.zeros((T, N))
        self.holdback_in = np.zeros((T, N)); self.holdback_out = np.zeros((T, N)); self.forfeits = np.zeros((T, N))
        self.cost = np.zeros((T, N)); self.entry = np.zeros((T, N))
        self.audit_cost = np.zeros(T)
        self.bond = np.zeros(N)
        self._settled = 0

    def fund(self, t: int, job: int, provider: int, amount: float, escrow: dict, owner: dict) -> None:
        if not np.isfinite(amount) or amount < 0:
            raise ValueError("payment must be finite and non-negative")
        escrow[job] = escrow.get(job, 0.0) + amount
        owner[job] = provider
        self.funding[t, provider] += amount

    def charge_cost(self, t: int, provider: int, amount: float) -> None:
        self.cost[t, provider] += amount

    def charge_entry(self, t: int, provider: int, amount: float) -> None:
        self.entry[t, provider] += amount

    def charge_audit(self, t: int, amount: float) -> None:
        self.audit_cost[t] += amount

    def recent_receipts(self) -> np.ndarray:
        if self._settled == 0:
            return np.zeros(self.N)
        lo = max(0, self._settled - H_MAX)
        return self.released[lo:self._settled].sum(axis=0)

    def settle(self, t: int, escrow: dict, owner: dict, cons: Consequences, failed_jobs_of: dict) -> None:
        released = np.zeros(self.N)
        for job, amount in escrow.items():
            p = owner[job]
            refund = min(cons.refunds.get(job, 0.0), amount)
            self.refunds[t, p] += refund
            released[p] += amount - refund
        for ident, amount in cons.forfeits.items():
            self.bond[ident] -= amount
            self.forfeits[t, ident] += amount
        for ident, amount in cons.releases.items():
            self.bond[ident] -= amount
            self.holdback_out[t, ident] += amount
        for ident, amount in cons.holdbacks.items():
            take = min(amount, released[ident])
            released[ident] -= take
            self.holdback_in[t, ident] += take
            self.bond[ident] += take
        self.released[t] += released
        self._settled = t + 1
        excess = np.maximum(self.bond - self.recent_receipts(), 0.0)
        self.bond -= excess
        self.holdback_out[t] += excess
        escrow.clear()
        owner.clear()

    def terminal_settlement(self) -> None:
        t = max(self._settled - 1, 0)
        self.holdback_out[t] += self.bond
        self.bond[:] = 0.0

    def profit(self) -> np.ndarray:
        return (self.released + self.holdback_out - self.cost - self.entry).sum(axis=0)

    def buyer_credit(self) -> float:
        return float(self.refunds.sum() + self.forfeits.sum())

    def check_conservation(self, escrow_outstanding: float) -> None:
        lhs = self.funding.sum()
        rhs = (self.released.sum() + self.refunds.sum() + self.holdback_out.sum()
               + self.forfeits.sum() + self.bond.sum() + escrow_outstanding)
        if not (np.isfinite(lhs) and np.isfinite(rhs)):
            raise AssertionError("non-finite ledger totals")
        if abs(lhs - rhs) > 1e-9:
            raise AssertionError(f"cash not conserved: funding {lhs:.9f} vs {rhs:.9f}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/ledger.py tests/test_ledger.py
git commit -m "feat: per-round ledger with bonds, forfeits, releases, forced release, conservation"
```

---

### Task 6: Harness validators for every rule output

**Files:**
- Create: `sim/checks.py`
- Test: `tests/test_checks.py`

**Interfaces:**
- Produces, each raising `ValueError` naming the violation: `validate_assignment(assignment, values_t, offers, view)`, `validate_payments(payments, assignment, values_t, offers)`, `validate_audits(audit_list, assignment, view)`, `validate_consequences(cons, records, escrow, owner, bond, recent_receipts, active)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_checks.py
import numpy as np
import pytest
from sim.checks import validate_assignment, validate_payments, validate_audits, validate_consequences
from sim.mechanisms.base import Offer, StateView, Consequences, AuditRecord


def view(N=3, caps=(1, 2, 1), banned=(0, 0, 0), t=0, audits_left=5):
    return StateView(t=t, T=10, N=N, audits_left=audits_left, audit_u=0.5, audit_key=np.zeros(4),
                     banned_until=np.array(banned), bond=np.zeros(N), capacity=np.array(caps),
                     escrow={}, history=(), memory={})


def test_assignment_rejects_abstainer_banned_capacity_and_bad_job():
    values = np.array([1.0, 1.0, 1.0, 1.0])
    offers = {0: Offer(0.9, 0.1), 1: Offer(0.9, 0.1)}
    validate_assignment({0: 0, 1: 1, 2: 1}, values, offers, view())
    with pytest.raises(ValueError, match="offer"):
        validate_assignment({0: 2}, values, offers, view())
    with pytest.raises(ValueError, match="banned"):
        validate_assignment({0: 0}, values, offers, view(banned=(5, 0, 0)))
    with pytest.raises(ValueError, match="capacity"):
        validate_assignment({0: 0, 1: 0}, values, offers, view())
    with pytest.raises(ValueError, match="job"):
        validate_assignment({7: 0}, values, offers, view())


def test_payments_cover_assignment_and_respect_acceptance():
    values = np.array([1.0, 0.5])
    offers = {0: Offer(0.8, 0.1)}
    validate_payments({0: 0.8}, {0: 0}, values, offers)
    with pytest.raises(ValueError, match="accept"):
        validate_payments({0: 0.81}, {0: 0}, values, offers)
    with pytest.raises(ValueError, match="payments"):
        validate_payments({}, {0: 0}, values, offers)
    with pytest.raises(ValueError, match="finite"):
        validate_payments({0: float("nan")}, {0: 0}, values, offers)


def test_audits_unique_served_within_allowance():
    validate_audits([0, 1], {0: 0, 1: 1}, view(audits_left=2))
    with pytest.raises(ValueError, match="unique"):
        validate_audits([0, 0], {0: 0, 1: 1}, view())
    with pytest.raises(ValueError, match="served"):
        validate_audits([3], {0: 0, 1: 1}, view())
    with pytest.raises(ValueError, match="allowance"):
        validate_audits([0, 1], {0: 0, 1: 1}, view(audits_left=1))


def test_consequences_require_failed_records_and_respect_caps():
    recs = (AuditRecord(job=0, provider=0, delivered=0.5, claim=0.9, failed=True),
            AuditRecord(job=1, provider=1, delivered=0.9, claim=0.9, failed=False))
    escrow, owner = {0: 0.8, 1: 0.8, 2: 0.8}, {0: 0, 1: 1, 2: 0}
    bond = np.array([0.5, 0.0, 0.0]); recent = np.array([1.0, 1.0, 0.0]); active = {0, 1}
    ok = lambda c: validate_consequences(c, recs, escrow, owner, bond, recent, active)
    ok(Consequences(refunds={0: 0.8}, bans={0: 10}, forfeits={0: 0.5}))
    for bad, msg in [
        (Consequences(refunds={1: 0.1}), "failed"), (Consequences(refunds={2: 0.1}), "failed"),
        (Consequences(bans={1: 5}), "failed"), (Consequences(bans={0: 51}), "ban"),
        (Consequences(bans={0: 2.5}), "integer"), (Consequences(holdbacks={0: 0.6}), "hold-back"),
        (Consequences(forfeits={0: 0.6}), "forfeit"), (Consequences(forfeits={1: 0.0001}), "forfeit"),
        (Consequences(forfeits={0: 0.3}, releases={0: 0.3}), "release"),
        (Consequences(refunds={0: float("nan")}), "finite"),
    ]:
        with pytest.raises(ValueError, match=msg):
            ok(bad)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_checks.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.checks'`

- [ ] **Step 3: Write the implementation**

```python
# sim/checks.py
from __future__ import annotations

import math

import numpy as np

from .mechanisms.base import AuditRecord, Consequences, L_MAX, Offers, StateView


def _finite(x) -> bool:
    return isinstance(x, (int, float, np.floating, np.integer)) and math.isfinite(float(x))


def validate_assignment(assignment: dict[int, int], values_t: np.ndarray, offers: Offers, view: StateView) -> None:
    J = len(values_t)
    counts = np.zeros(view.N, dtype=np.int64)
    for j, i in assignment.items():
        if not (0 <= int(j) < J):
            raise ValueError(f"assignment names job {j} out of range")
        if i not in offers:
            raise ValueError(f"assignment to provider {i} with no offer")
        if not view.is_active(i):
            raise ValueError(f"assignment to banned provider {i}")
        counts[i] += 1
    over = np.flatnonzero(counts > view.capacity)
    if over.size:
        raise ValueError(f"capacity exceeded for providers {over.tolist()}")


def validate_payments(payments: dict[int, float], assignment: dict[int, int], values_t: np.ndarray, offers: Offers) -> None:
    if set(payments.keys()) != set(assignment.keys()):
        raise ValueError("payments must cover exactly the assigned jobs")
    for j, p in payments.items():
        if not _finite(p) or p < 0:
            raise ValueError(f"payment for job {j} must be finite and non-negative")
        if p > values_t[j] * offers[assignment[j]].claim + 1e-12:
            raise ValueError(f"payment for job {j} exceeds what the buyer accepts")


def validate_audits(audit_list: list[int], assignment: dict[int, int], view: StateView) -> None:
    if len(set(audit_list)) != len(audit_list):
        raise ValueError("audit list must be unique")
    for j in audit_list:
        if j not in assignment:
            raise ValueError(f"audit of unserved job {j}")
    if len(audit_list) > view.audits_left:
        raise ValueError("audit list exceeds the remaining allowance")


def validate_consequences(cons: Consequences, records: tuple[AuditRecord, ...], escrow: dict, owner: dict,
                          bond: np.ndarray, recent_receipts: np.ndarray, active: set[int]) -> None:
    failed_jobs = {r.job for r in records if r.failed}
    failed_idents = {r.provider for r in records if r.failed}
    for job, amt in cons.refunds.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"refund for job {job} must be finite and non-negative")
        if job not in failed_jobs:
            raise ValueError(f"refund for job {job} without a failed audit")
        if amt > escrow.get(job, 0.0) + 1e-12:
            raise ValueError(f"refund for job {job} exceeds its escrow")
    for ident, rounds in cons.bans.items():
        if isinstance(rounds, bool) or not isinstance(rounds, (int, np.integer)):
            raise ValueError(f"ban for identity {ident} must be an integer number of rounds")
        if ident not in failed_idents:
            raise ValueError(f"ban for identity {ident} without a failed audit")
        if not (0 < rounds <= L_MAX):
            raise ValueError(f"ban for identity {ident} must be in 1..{L_MAX}")
    bond_after = np.array(bond, dtype=float)
    for ident, amt in cons.forfeits.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"forfeit for identity {ident} must be finite and non-negative")
        if ident not in failed_idents:
            raise ValueError(f"forfeit for identity {ident} without a failed audit")
        cap_escrow = sum(escrow.get(j, 0.0) for j in failed_jobs if owner.get(j) == ident)
        if amt > min(bond_after[ident], cap_escrow) + 1e-12:
            raise ValueError(f"forfeit for identity {ident} exceeds its bond or its failed escrow")
        bond_after[ident] -= amt
    for ident, amt in cons.releases.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"release for identity {ident} must be finite and non-negative")
        if amt > bond_after[ident] + 1e-12:
            raise ValueError(f"release for identity {ident} exceeds its bond")
        bond_after[ident] -= amt
    for ident, amt in cons.holdbacks.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"hold-back for identity {ident} must be finite and non-negative")
        if ident not in active:
            raise ValueError(f"hold-back for identity {ident} without an offer this round")
        if bond_after[ident] + amt > recent_receipts[ident] + 1e-12:
            raise ValueError(f"hold-back for identity {ident} exceeds the H_MAX-round receipts cap")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_checks.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/checks.py tests/test_checks.py
git commit -m "feat: harness validators for assignment, payments, audits, and consequences"
```

---

### Task 7: Policies, B1 posted prices, and the validated episode loop

**Files:**
- Create: `sim/policies/__init__.py`, `sim/policies/base.py`, `sim/policies/honest.py`, `sim/policies/fixed_cheat.py`, `sim/policies/twin.py`, `sim/mechanisms/posted.py`, `sim/market.py`
- Test: `tests/test_policies.py`, `tests/test_posted.py`, `tests/test_market.py`

**Interfaces:**
- Produces: `ProviderHistory` (per-round lists `served, payment, audited, failed, refunded, banned_until`; `append(...)`); `ProviderView(i, params, t, posted_prices, history, policy_seed)` with cached `rng`; `Action(effort, offer, exit=False)`; `validate_action(action, params)`; `HonestMax()`; `FixedCheat(u, m, s, w, clip)`; `Twin(policy)`; `PostedPrices(P1, P2, P3)` with `TIERS`, `tier_of`, `describe()`; `EpisodeResult(sstar, profit, value, cost, entry, audit_cost, served, audits, failures, claims, efforts, buyer_surplus, W, history, ledger)`; `run_episode(cfg, rule, policies, seed, draws=None, sstar=None)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_policies.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.policies.base import ProviderView, ProviderHistory, Action, validate_action
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.twin import Twin
from sim.mechanisms.base import Offer


def view(i=0, t=0, seed=0):
    cfg = MarketConfig.default()
    return ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=None, history=ProviderHistory(), policy_seed=seed)


def test_honest_max_claims_effort_bids_cost():
    p = MarketConfig.default().providers[3]
    a = HonestMax().act(view(i=3))
    assert a.effort == pytest.approx(p.q_max) and a.offer.claim == pytest.approx(p.q_max)
    assert a.offer.bid == pytest.approx(p.a + p.b * p.q_max) and a.exit is False


def test_fixed_cheat_knobs_and_domains():
    p = MarketConfig.default().providers[0]   # q_max 0.6
    a = FixedCheat(u=0.5, m=0.4, s=0.1, w=0.5, clip=0).act(view(i=0))
    assert a.effort == pytest.approx(0.3) and a.offer.claim == pytest.approx(0.6)
    assert a.offer.bid == pytest.approx(1.5 * (p.a + p.b * 0.3))
    for bad in (dict(u=-0.1, m=0, s=0, w=0, clip=0), dict(u=0, m=1.1, s=0, w=0, clip=0),
                dict(u=0, m=0, s=0.4, w=0, clip=0), dict(u=0, m=0, s=0, w=2.5, clip=0),
                dict(u=0, m=0, s=0, w=0, clip=2), dict(u=0, m=0, s=0, w=0, clip=0.5)):
        with pytest.raises(ValueError):
            FixedCheat(**bad)


def test_clip_knob_and_twin_never_inflate():
    a = FixedCheat(u=0.5, m=0.9, s=0.0, w=0.0, clip=1).act(view(i=0))
    assert a.offer.claim <= a.effort + 1e-12
    base = FixedCheat(u=0.0, m=1.0, s=0.0, w=0.0, clip=0)
    raw, tw = base.act(view(i=0)), Twin(base).act(view(i=0))
    assert raw.offer.claim > raw.effort
    assert tw.effort == pytest.approx(raw.effort) and tw.offer.claim == pytest.approx(raw.effort)
    assert tw.offer.bid == pytest.approx(raw.offer.bid)


def test_honest_max_equals_its_twin():
    for i in range(10):
        assert HonestMax().act(view(i=i)) == Twin(HonestMax()).act(view(i=i))


def test_validate_action():
    p = MarketConfig.default().providers[0]
    validate_action(Action(effort=0.6, offer=Offer(0.5, 0.1)), p)
    for bad in (Action(effort=0.61, offer=Offer(0.5, 0.1)), Action(effort=-0.01, offer=None), Action(effort=float("nan"), offer=None)):
        with pytest.raises(ValueError):
            validate_action(bad, p)
    with pytest.raises(NotImplementedError):
        validate_action(Action(effort=0.5, offer=None, exit=True), p)


def test_view_rng_is_cached_and_seeded():
    v = view(seed=5)
    x1, x2 = v.rng.random(), v.rng.random()
    ref = np.random.default_rng(5)
    assert x1 == ref.random() and x2 == ref.random()
```

```python
# tests/test_posted.py
import numpy as np
import pytest
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.base import Offer, StateView


def view(N, caps, t=0, banned=None, tie=None, J=1):
    tie = np.zeros((J, N)) if tie is None else tie
    return StateView(t=t, T=5, N=N, audits_left=0, audit_u=0.5, audit_key=np.zeros(J),
                     banned_until=np.zeros(N, dtype=np.int64) if banned is None else np.array(banned),
                     bond=np.zeros(N), capacity=np.array(caps), escrow={}, history=(), memory={"tie_key": tie})


def test_tier_boundaries():
    r = PostedPrices(0.2, 0.4, 0.6)
    assert r.tier_of(0.0) == 0 and r.tier_of(0.49) == 0
    assert r.tier_of(0.5) == 1 and r.tier_of(0.79) == 1
    assert r.tier_of(0.8) == 2 and r.tier_of(1.0) == 2


def test_prefers_highest_tier_and_respects_acceptance():
    r = PostedPrices(0.2, 0.4, 0.6)
    offers = {0: Offer(0.4, 0.0), 1: Offer(0.9, 0.0)}
    asg = r.allocate(np.array([0.7]), offers, view(2, (1, 1)))
    assert asg == {0: 1}
    assert r.price(asg, np.array([0.7]), offers, view(2, (1, 1))) == {0: pytest.approx(0.6)}


def test_no_acceptable_tier_leaves_job_unserved():
    assert PostedPrices(0.5, 0.7, 0.9).allocate(np.array([0.6]), {0: Offer(0.6, 0.0)}, view(1, (1,))) == {}


def test_banned_provider_not_eligible():
    assert PostedPrices(0.2, 0.4, 0.6).allocate(np.array([1.0]), {0: Offer(0.9, 0.0)}, view(1, (1,), t=2, banned=[4])) == {}


def test_tie_break_uses_smallest_key():
    offers = {0: Offer(0.9, 0.0), 1: Offer(0.9, 0.0)}
    assert PostedPrices(0.2, 0.4, 0.6).allocate(np.array([1.0]), offers, view(2, (1, 1), tie=np.array([[0.7, 0.2]]))) == {0: 1}


def test_describe_fields():
    d = PostedPrices(0.2, 0.4, 0.6).describe()
    assert set(d) >= {"allocation", "pricing", "audit_selection", "audit_tolerance", "failed_audit", "ban_length", "holdback"}
```

```python
# tests/test_market.py
import numpy as np
import pytest
from sim.config import MarketConfig, ProviderParams
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.rng import make_draws


def b1():
    return PostedPrices(0.25, 0.40, 0.55)


def honest(n):
    return [HonestMax() for _ in range(n)]


def test_same_seed_same_result():
    cfg = MarketConfig.default()
    a, b = run_episode(cfg, b1(), honest(cfg.N), 5), run_episode(cfg, b1(), honest(cfg.N), 5)
    assert a.W == b.W and np.array_equal(a.profit, b.profit)
    assert np.array_equal(a.claims, b.claims, equal_nan=True)


def test_deviation_does_not_change_draw_contents():
    cfg = MarketConfig.default()
    d = make_draws(cfg, 9)
    snap = {k: getattr(d, k).copy() for k in ("values", "noise", "tie_key", "audit_u", "audit_key", "policy_seed")}
    dev = honest(cfg.N); dev[0] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    a = run_episode(cfg, b1(), honest(cfg.N), 9, draws=d)
    b = run_episode(cfg, b1(), dev, 9, draws=d)
    for k, arr in snap.items():
        assert np.array_equal(arr, getattr(d, k))
    assert not np.array_equal(a.profit, b.profit)


def test_capacity_above_jobs_runs():
    c0 = MarketConfig.default()
    big = tuple(ProviderParams(p.q_max, p.a, p.b, k=80) for p in c0.providers)
    cfg = MarketConfig(N=10, J=50, T=3, sigma=0.05, e=0.0, v_min=0.6, v_max=1.4, providers=big, alpha=0.05, budget=0.0)
    assert run_episode(cfg, b1(), honest(10), 1).served.sum() <= 150


def test_tied_values_deterministic():
    c0 = MarketConfig.default()
    cfg = MarketConfig(N=10, J=50, T=5, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0, providers=c0.providers, alpha=0.05, budget=0.0)
    a, b = run_episode(cfg, b1(), honest(10), 2), run_episode(cfg, b1(), honest(10), 2)
    assert np.array_equal(a.served, b.served)


def test_history_records_every_round():
    cfg = MarketConfig.default()
    res = run_episode(cfg, b1(), honest(cfg.N), 0)
    assert len(res.history) == cfg.T and res.history[0].t == 0 and res.history[-1].t == cfg.T - 1
    assert all(len(rec.audits) == 0 for rec in res.history)


def test_invalid_rule_output_is_rejected_before_money_moves():
    class BadRule(PostedPrices):
        def allocate(self, values_t, offers, view):
            return {j: 0 for j in range(7)}   # capacity is 6
    cfg = MarketConfig.default()
    with pytest.raises(ValueError, match="capacity"):
        run_episode(cfg, BadRule(0.25, 0.40, 0.55), honest(cfg.N), 0)


def test_rule_cannot_mutate_economic_state():
    class Sneaky(PostedPrices):
        def allocate(self, values_t, offers, view):
            view.banned_until[:] = 999
            return super().allocate(values_t, offers, view)
    cfg = MarketConfig.default()
    with pytest.raises(ValueError, match="read-only"):
        run_episode(cfg, Sneaky(0.25, 0.40, 0.55), honest(cfg.N), 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_policies.py tests/test_posted.py tests/test_market.py -v`
Expected: FAIL with `ModuleNotFoundError` on `sim.policies`

- [ ] **Step 3: Write the implementation**

```python
# sim/policies/__init__.py
```

```python
# sim/policies/base.py
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
```

```python
# sim/policies/honest.py
from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class HonestMax:
    name = "honest_max"

    def act(self, view: ProviderView) -> Action:
        p = view.params
        return Action(effort=p.q_max, offer=Offer(claim=p.q_max, bid=p.a + p.b * p.q_max))
```

```python
# sim/policies/fixed_cheat.py
from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class FixedCheat:
    """D1 (spec 5.3). Knobs: u, m in [0,1]; s in [0,0.3]; w in [0,2]; clip in {0,1}."""
    name = "fixed_cheat"

    def __init__(self, u: float, m: float, s: float, w: float, clip: int) -> None:
        if not (0.0 <= u <= 1.0 and 0.0 <= m <= 1.0 and 0.0 <= s <= 0.3 and 0.0 <= w <= 2.0):
            raise ValueError("D1 knob outside its domain")
        if isinstance(clip, bool) or clip not in (0, 1) or int(clip) != clip:
            raise ValueError("clip must be exactly 0 or 1")
        self.u, self.m, self.s, self.w, self.clip = float(u), float(m), float(s), float(w), int(clip)

    def act(self, view: ProviderView) -> Action:
        p = view.params
        effort = p.q_max * (1.0 - self.u)
        claim = min(1.0, max(0.0, effort + self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + self.w) * (p.a + p.b * effort)))
```

```python
# sim/policies/twin.py
from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class Twin:
    """Truthful twin: same policy, market-facing claim clipped to <= effort."""

    def __init__(self, policy) -> None:
        self.policy = policy
        self.name = f"twin({getattr(policy, 'name', 'policy')})"

    def act(self, view: ProviderView) -> Action:
        a = self.policy.act(view)
        if a.offer is None:
            return a
        return Action(effort=a.effort, offer=Offer(claim=min(a.offer.claim, a.effort), bid=a.offer.bid), exit=a.exit)
```

```python
# sim/mechanisms/posted.py
from __future__ import annotations

import numpy as np

from .base import AuditRecord, Consequences, Mechanism, Offers, StateView

TIERS = ((0.0, 0.5), (0.5, 0.8), (0.8, 1.0001))


class PostedPrices(Mechanism):
    """B1 (spec 4.1). Tie-breaks use the precomputed key view.memory['tie_key'][j, i]."""
    name = "B1_posted"
    tol = None

    def __init__(self, P1: float, P2: float, P3: float) -> None:
        if not (0.0 < P1 < P2 < P3):
            raise ValueError("need 0 < P1 < P2 < P3")
        self.prices = (float(P1), float(P2), float(P3))

    @staticmethod
    def tier_of(claim: float) -> int:
        for k, (lo, hi) in enumerate(TIERS):
            if lo <= claim < hi:
                return k
        return 2

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        N = view.N
        cap = np.array(view.capacity, dtype=np.int64)
        tier = np.full(N, -1, dtype=np.int64)
        claim = np.zeros(N)
        for i, off in offers.items():
            if view.is_active(i):
                tier[i] = self.tier_of(off.claim)
                claim[i] = off.claim
        price = np.where(tier >= 0, np.array(self.prices)[np.clip(tier, 0, 2)], np.inf)
        tie = view.memory["tie_key"]
        out: dict[int, int] = {}
        for j in np.argsort(-values_t, kind="stable"):
            v = float(values_t[j])
            mask = (cap > 0) & (tier >= 0) & (v * claim >= price)
            if not mask.any():
                continue
            best = tier[mask].max()
            cands = np.flatnonzero(mask & (tier == best))
            chosen = int(cands[np.argmin(tie[j, cands])])
            out[int(j)] = chosen
            cap[chosen] -= 1
        return out

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return {j: self.prices[self.tier_of(offers[i].claim)] for j, i in assignment.items()}

    def audit(self, assignment, view) -> list[int]:
        return []

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        return Consequences()

    def describe(self) -> dict[str, str]:
        return {"allocation": "descending value; highest accepted tier; random within tier",
                "pricing": "posted tier price", "audit_selection": "none", "audit_tolerance": "none",
                "failed_audit": "none", "ban_length": "0", "holdback": "none"}
```

```python
# sim/market.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .checks import validate_assignment, validate_audits, validate_consequences, validate_payments
from .config import MarketConfig
from .firstbest import first_best_episode
from .ledger import Ledger
from .mechanisms.base import AuditRecord, Consequences, Offer, RoundRecord, StateView
from .policies.base import ProviderHistory, ProviderView, validate_action
from .rng import Draws, make_draws


@dataclass
class EpisodeResult:
    sstar: float
    profit: np.ndarray
    value: float
    cost: float
    entry: float
    audit_cost: float
    served: np.ndarray
    audits: np.ndarray
    failures: np.ndarray
    claims: np.ndarray
    efforts: np.ndarray
    buyer_surplus: float
    W: float
    history: tuple[RoundRecord, ...]
    ledger: Ledger


def run_episode(cfg: MarketConfig, rule, policies, seed: int, draws: Draws | None = None, sstar: float | None = None) -> EpisodeResult:
    cfg.validate()
    if len(policies) != cfg.N:
        raise ValueError("one policy per provider")
    d = draws if draws is not None else make_draws(cfg, seed)
    sstar_v = first_best_episode(cfg, d) if sstar is None else float(sstar)
    rule.bind(cfg)
    N, T, alpha = cfg.N, cfg.T, cfg.alpha
    allowance = int(np.floor(cfg.budget / alpha + 1e-12)) if alpha > 0 else 0
    ledger = Ledger(N, T)
    banned_until = np.zeros(N, dtype=np.int64)
    caps = np.array([p.k for p in cfg.providers], dtype=np.int64)
    a_arr = np.array([p.a for p in cfg.providers]); b_arr = np.array([p.b for p in cfg.providers])
    histories = [ProviderHistory() for _ in range(N)]
    posted = getattr(rule, "prices", None)
    memory: dict = {}
    records_all: list[RoundRecord] = []
    served = np.zeros((T, N), dtype=np.int64); audits = np.zeros(T, dtype=np.int64)
    failures = np.zeros((T, N), dtype=np.int64); claims = np.full((T, N), np.nan); efforts = np.zeros((T, N))
    value_total = 0.0
    tol = rule.tol

    for t in range(T):
        values_t = d.values[t].copy()
        offers: dict[int, Offer] = {}
        effort = np.zeros(N)
        for i in range(N):
            if t < banned_until[i]:
                continue
            act = policies[i].act(ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=posted,
                                               history=histories[i], policy_seed=int(d.policy_seed[t, i])))
            validate_action(act, cfg.providers[i])
            effort[i] = float(act.effort); efforts[t, i] = effort[i]
            if act.offer is not None:
                offers[i] = Offer(claim=float(act.offer.claim), bid=float(act.offer.bid))
                claims[t, i] = offers[i].claim
        memory["tie_key"] = d.tie_key[t]
        hist = tuple(records_all)
        view = StateView(t=t, T=T, N=N, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                         banned_until=banned_until, bond=ledger.bond, capacity=caps, escrow={}, history=hist, memory=memory)
        try:
            assignment = rule.allocate(values_t, offers, view)
            payments = rule.price(assignment, values_t, offers, view)
        except ValueError as exc:
            if "read-only" in str(exc):
                raise ValueError("rule attempted to write read-only state") from exc
            raise
        validate_assignment(assignment, values_t, offers, view)
        validate_payments(payments, assignment, values_t, offers)
        escrow: dict[int, float] = {}; owner: dict[int, int] = {}
        for j, i in assignment.items():
            ledger.fund(t, j, i, payments[j], escrow, owner)
        delivered: dict[int, float] = {}
        if assignment:
            jobs = np.fromiter(assignment.keys(), dtype=np.int64, count=len(assignment))
            provs = np.fromiter(assignment.values(), dtype=np.int64, count=len(assignment))
            slots = np.zeros(len(provs), dtype=np.int64); seen = np.zeros(N, dtype=np.int64)
            for n, i in enumerate(provs):
                slots[n] = seen[i]; seen[i] += 1
            y = effort[provs] + d.noise[t, provs, slots]
            value_total += float((values_t[jobs] * y).sum())
            counts = np.bincount(provs, minlength=N)
            ledger.cost[t] += counts * (a_arr + b_arr * effort)
            served[t] = counts
            delivered = dict(zip(jobs.tolist(), y.tolist()))
        view_a = StateView(t=t, T=T, N=N, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                           banned_until=banned_until, bond=ledger.bond, capacity=caps, escrow=escrow, history=hist, memory=memory)
        to_audit = list(rule.audit(assignment, view_a))
        validate_audits(to_audit, assignment, view_a)
        records = tuple(AuditRecord(job=j, provider=assignment[j], delivered=delivered[j], claim=offers[assignment[j]].claim,
                                    failed=(tol is not None and delivered[j] < offers[assignment[j]].claim - tol))
                        for j in to_audit)
        allowance -= len(records)
        ledger.charge_audit(t, alpha * len(records))
        audits[t] = len(records)
        cons = rule.enforce(records, view_a)
        if not isinstance(cons, Consequences):
            raise TypeError("enforce must return a Consequences object")
        validate_consequences(cons, records, escrow, owner, ledger.bond, ledger.recent_receipts(), set(offers.keys()))
        failed_jobs_of: dict[int, list[int]] = {}
        for r in records:
            if r.failed:
                failures[t, r.provider] += 1
                failed_jobs_of.setdefault(r.provider, []).append(r.job)
        for ident, rounds in cons.bans.items():
            banned_until[ident] = max(int(banned_until[ident]), t + int(rounds) + 1)
        refunded = np.zeros(N)
        for j, amt in cons.refunds.items():
            refunded[owner[j]] += amt
        ledger.settle(t, escrow, owner, cons, failed_jobs_of)
        ledger.check_conservation(escrow_outstanding=0.0)
        records_all.append(RoundRecord(t=t, offers=dict(offers), assignment=dict(assignment), payments=dict(payments),
                                       audits=records, consequences=cons))
        audited_by = np.bincount([r.provider for r in records], minlength=N) if records else np.zeros(N, dtype=np.int64)
        for i in range(N):
            histories[i].append(int(served[t, i]), float(ledger.funding[t, i]), int(audited_by[i]), int(failures[t, i]),
                                float(refunded[i]), int(banned_until[i]))

    ledger.terminal_settlement()
    ledger.check_conservation(escrow_outstanding=0.0)
    cost = float(ledger.cost.sum()); entry = float(ledger.entry.sum()); audit_cost = float(ledger.audit_cost.sum())
    W = value_total - cost - entry - audit_cost
    buyer_surplus = value_total - float(ledger.funding.sum()) + ledger.buyer_credit()
    return EpisodeResult(sstar=sstar_v, profit=ledger.profit(), value=value_total, cost=cost, entry=entry,
                         audit_cost=audit_cost, served=served, audits=audits, failures=failures, claims=claims,
                         efforts=efforts, buyer_surplus=buyer_surplus, W=W, history=tuple(records_all), ledger=ledger)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_policies.py tests/test_posted.py tests/test_market.py -v`
Expected: PASS (19 tests). The read-only test passes because NumPy raises `ValueError: assignment destination is read-only`, which the harness re-raises with "read-only" in the message.

- [ ] **Step 5: Commit**

```bash
git add sim/policies sim/mechanisms/posted.py sim/market.py tests/test_policies.py tests/test_posted.py tests/test_market.py
git commit -m "feat: policies with validation, B1 posted prices, validated episode loop with audit records"
```

---

### Task 8: B2 with the integer spread audit schedule

**Files:**
- Create: `sim/mechanisms/audit_random.py`, `sim/mechanisms/posted_audit.py`
- Test: `tests/test_posted_audit.py`

**Interfaces:**
- Produces: `spread_audit_count(allowance_left, t, T, served_count, cap_per_round, audit_u) -> int`; `RandomAuditMixin` (`tol`, `L`, `cap_per_round`, `T`, `bind`, `audit`, `enforce`); `PostedRandomAudit(P1, P2, P3, tol, L)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_posted_audit.py
import numpy as np
import pytest
from scipy import stats
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.audit_random import spread_audit_count
from sim.mechanisms.base import Consequences
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.rng import make_draws


def b2(tol=0.12, L=10):
    return PostedRandomAudit(0.25, 0.40, 0.55, tol=tol, L=L)


def cfgb(budget, T=200, sigma=0.05):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def honest(n):
    return [HonestMax() for _ in range(n)]


def test_spread_count_exact_rounding_and_caps():
    assert spread_audit_count(100, 0, 8, 1000, 25, audit_u=0.49) == 13   # target 12.5
    assert spread_audit_count(100, 0, 8, 1000, 25, audit_u=0.51) == 12
    assert spread_audit_count(0, 5, 10, 50, 10, 0.3) == 0
    assert spread_audit_count(1, 9, 10, 50, 10, 0.99) == 1
    assert spread_audit_count(1000, 0, 10, 50, 1, 0.0) == 1
    assert spread_audit_count(1000, 0, 1, 3, 1000, 0.0) == 3


def test_integer_allowance_is_fully_spent_when_affordable():
    cfg = cfgb(budget=2.0)   # floor(2.0 / 0.05) = 40 audits
    for seed in range(5):
        res = run_episode(cfg, b2(L=0), honest(cfg.N), seed)
        assert res.audits.sum() == 40
        assert res.audit_cost == pytest.approx(40 * cfg.alpha)
        assert res.audits.max() <= 1


def test_budget_never_exceeded_and_cap_holds():
    cfg = cfgb(budget=3.0)
    for seed in range(5):
        res = run_episode(cfg, b2(), honest(cfg.N), seed)
        assert res.audits.sum() <= int(np.floor(cfg.budget / cfg.alpha + 1e-12))
        assert res.audits.max() <= max(1, int(np.floor(2 * cfg.budget / (cfg.T * cfg.alpha))))


def test_audit_count_in_round_is_action_independent():
    cfg = cfgb(budget=20.0, T=50)
    d = make_draws(cfg, 3)
    dev = honest(cfg.N); dev[0] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    a = run_episode(cfg, b2(L=0), honest(cfg.N), 3, draws=d)
    b = run_episode(cfg, b2(L=0), dev, 3, draws=d)
    assert np.array_equal(a.audits, b.audits)


def test_honest_failure_rate_matches_formula():
    cfg = cfgb(budget=40.0, T=100)
    tol = 0.08
    fails = auds = 0
    for seed in range(6):
        res = run_episode(cfg, b2(tol=tol, L=0), honest(cfg.N), seed)
        fails += res.failures.sum(); auds += res.audits.sum()
    p = stats.norm.cdf(-tol / cfg.sigma)
    assert abs(fails / auds - p) < 4 * np.sqrt(p * (1 - p) / auds) + 0.005


def test_spread_halves_hypergeometric_criterion():
    cfg = cfgb(budget=2.0)
    diffs = []
    for seed in range(200):
        res = run_episode(cfg, b2(L=0), honest(cfg.N), seed)
        diffs.append(abs(int(res.audits[:100].sum()) - int(res.audits[100:].sum())))
    hg = stats.hypergeom(200, 100, 40)
    k = np.arange(0, 41)
    expected = float((hg.pmf(k) * np.abs(2 * k - 40)).sum())
    sd = float(np.sqrt((hg.pmf(k) * (np.abs(2 * k - 40) - expected) ** 2).sum()))
    assert abs(np.mean(diffs) - expected) <= 2 * sd / np.sqrt(200) + 0.5


def test_all_providers_banned_round_is_fine():
    cfg = cfgb(budget=50.0, T=30)
    res = run_episode(cfg, b2(tol=-10.0, L=20), honest(cfg.N), 0)
    assert np.isfinite(res.W) and (res.served.sum(axis=1) == 0).any()


def test_negative_delivery_exact_contribution_and_failure():
    c = MarketConfig.default()
    cfg = MarketConfig(N=1, J=1, T=1, sigma=2.0, e=0.0, v_min=1.0, v_max=1.0,
                       providers=(c.providers[9],), alpha=0.05, budget=0.05)
    d = make_draws(cfg, 0)
    res = run_episode(cfg, b2(tol=0.0, L=0), honest(1), 0, draws=d)
    y = 1.0 + d.noise[0, 0, 0]
    assert res.value == pytest.approx(1.0 * y)
    assert res.failures.sum() == (1 if y < 1.0 else 0)


def test_failed_audit_without_refund_still_counts_as_failure():
    class NoRefund(PostedRandomAudit):
        def enforce(self, records, view):
            return Consequences()
    cfg = cfgb(budget=40.0, T=50)
    res = run_episode(cfg, NoRefund(0.25, 0.40, 0.55, tol=0.0, L=0), honest(cfg.N), 0)
    assert res.failures.sum() > 0 and res.ledger.refunds.sum() == 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_posted_audit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.mechanisms.audit_random'`

- [ ] **Step 3: Write the implementation**

```python
# sim/mechanisms/audit_random.py
from __future__ import annotations

import numpy as np

from .base import AuditRecord, Consequences, StateView


def spread_audit_count(allowance_left: int, t: int, T: int, served_count: int, cap_per_round: int, audit_u: float) -> int:
    """Spec 4.1 spread schedule on an integer allowance; t is zero-based."""
    if allowance_left <= 0:
        return 0
    target = allowance_left / (T - t)
    base = int(np.floor(target))
    n = base + (1 if audit_u < target - base else 0)
    return max(0, min(n, int(served_count), int(cap_per_round), int(allowance_left)))


class RandomAuditMixin:
    tol: float
    L: int
    cap_per_round: int = 1
    T: int = 1

    def bind(self, cfg) -> None:
        self.T = int(cfg.T)
        self.cap_per_round = max(1, int(np.floor(2.0 * cfg.budget / (cfg.T * cfg.alpha)))) if cfg.alpha > 0 else 0

    def audit(self, assignment: dict[int, int], view: StateView) -> list[int]:
        jobs = np.fromiter(assignment.keys(), dtype=np.int64, count=len(assignment))
        n = spread_audit_count(view.audits_left, view.t, self.T, len(jobs), self.cap_per_round, view.audit_u)
        if n == 0:
            return []
        order = np.argsort(view.audit_key[jobs], kind="stable")
        return jobs[order[:n]].tolist()

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        cons = Consequences()
        for r in records:
            if r.failed:
                cons.refunds[r.job] = float(view.escrow[r.job])
                if self.L > 0:
                    cons.bans[r.provider] = max(cons.bans.get(r.provider, 0), int(self.L))
        return cons
```

```python
# sim/mechanisms/posted_audit.py
from __future__ import annotations

from .audit_random import RandomAuditMixin
from .posted import PostedPrices


class PostedRandomAudit(RandomAuditMixin, PostedPrices):
    """B2 (spec 4.1)."""
    name = "B2_posted_random_audit"

    def __init__(self, P1: float, P2: float, P3: float, tol: float, L: int) -> None:
        PostedPrices.__init__(self, P1, P2, P3)
        self.tol = float(tol)
        self.L = int(L)

    def describe(self) -> dict[str, str]:
        d = PostedPrices.describe(self)
        d.update({"audit_selection": "uniform random among served jobs, spread schedule",
                  "audit_tolerance": f"{self.tol}", "failed_audit": "full refund",
                  "ban_length": f"{self.L}", "holdback": "none"})
        return d
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_posted_audit.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/mechanisms/audit_random.py sim/mechanisms/posted_audit.py tests/test_posted_audit.py
git commit -m "feat: B2 with integer spread audit schedule, action-independent selection, enforcement"
```

---

### Task 9: B3 second-score sequential auction

**Files:**
- Create: `sim/mechanisms/second_score.py`
- Test: `tests/test_second_score.py`

**Interfaces:**
- Produces: `SecondScore(tol, L)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_second_score.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.base import Offer, StateView
from sim.mechanisms.second_score import SecondScore
from sim.policies.honest import HonestMax


def view(N, caps, J=1, tie=None):
    tie = np.zeros((J, N)) if tie is None else tie
    return StateView(t=0, T=1, N=N, audits_left=0, audit_u=0.5, audit_key=np.zeros(J),
                     banned_until=np.zeros(N, dtype=np.int64), bond=np.zeros(N), capacity=np.array(caps),
                     escrow={}, history=(), memory={"tie_key": tie})


def test_worked_example_payment_is_three():
    r = SecondScore(tol=0.12, L=10)
    offers = {0: Offer(1.0, 1.0), 1: Offer(1.0, 3.0)}
    v = view(2, (1, 1))
    asg = r.allocate(np.array([10.0]), offers, v)
    assert asg == {0: 0}
    assert r.price(asg, np.array([10.0]), offers, v)[0] == pytest.approx(3.0)


def test_single_bidder_pays_value_times_claim():
    r = SecondScore(tol=0.12, L=10)
    offers = {0: Offer(0.9, 0.5)}
    v = view(1, (1,))
    asg = r.allocate(np.array([2.0]), offers, v)
    assert r.price(asg, np.array([2.0]), offers, v)[0] == pytest.approx(1.8)


def test_negative_score_not_eligible_and_capacity_respected():
    r = SecondScore(tol=0.12, L=10)
    assert r.allocate(np.array([0.6]), {0: Offer(0.5, 1.0)}, view(1, (1,))) == {}
    offers = {0: Offer(1.0, 0.1), 1: Offer(1.0, 0.5)}
    asg = r.allocate(np.array([1.0, 1.0, 1.0]), offers, view(2, (1, 5), J=3))
    assert list(asg.values()).count(0) == 1 and list(asg.values()).count(1) == 2


def test_tie_broken_by_key():
    offers = {0: Offer(1.0, 0.5), 1: Offer(1.0, 0.5)}
    assert SecondScore(tol=0.12, L=10).allocate(np.array([1.0]), offers, view(2, (1, 1), tie=np.array([[0.9, 0.1]]))) == {0: 1}


def test_full_episode_audits_and_runs():
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=50, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=2.0)
    res = run_episode(cfg, SecondScore(tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    assert res.audits.sum() == 40 and res.W > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_second_score.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.mechanisms.second_score'`

- [ ] **Step 3: Write the implementation**

```python
# sim/mechanisms/second_score.py
from __future__ import annotations

import numpy as np

from .audit_random import RandomAuditMixin
from .base import Mechanism, Offers, StateView


class SecondScore(RandomAuditMixin, Mechanism):
    """B3 (spec 4.1): sequential second-score auction with capacity; not truthful."""
    name = "B3_second_score"

    def __init__(self, tol: float, L: int) -> None:
        self.tol = float(tol)
        self.L = int(L)

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        N = view.N
        cap = np.array(view.capacity, dtype=np.int64)
        claim = np.zeros(N); bid = np.zeros(N); offered = np.zeros(N, dtype=bool)
        for i, off in offers.items():
            if view.is_active(i):
                claim[i], bid[i], offered[i] = off.claim, off.bid, True
        tie = view.memory["tie_key"]
        idx = np.arange(N)
        s2_map: dict[int, float] = {}
        out: dict[int, int] = {}
        for j in np.argsort(-values_t, kind="stable"):
            v = float(values_t[j])
            score = v * claim - bid
            mask = offered & (cap > 0) & (score >= 0)
            if not mask.any():
                continue
            top = score[mask].max()
            winners = np.flatnonzero(mask & (score == top))
            w = int(winners[np.argmin(tie[j, winners])])
            rest = score[mask & (idx != w)]
            s2_map[int(j)] = float(rest.max()) if rest.size else 0.0
            out[int(j)] = w
            cap[w] -= 1
        view.memory["second_scores"] = s2_map
        return out

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        s2 = view.memory.get("second_scores", {})
        return {j: float(values_t[j] * offers[i].claim - s2.get(j, 0.0)) for j, i in assignment.items()}

    def describe(self) -> dict[str, str]:
        return {"allocation": "descending value; highest score v*claim - bid wins; capacity respected",
                "pricing": "second score: v*claim minus runner-up score",
                "audit_selection": "uniform random among served jobs, spread schedule",
                "audit_tolerance": f"{self.tol}", "failed_audit": "full refund",
                "ban_length": f"{self.L}", "holdback": "none"}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_second_score.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/mechanisms/second_score.py tests/test_second_score.py
git commit -m "feat: B3 second-score sequential auction"
```

---

### Task 10: Metrics, gain and harm, shared harness tests across rules, information-boundary tests, run script

**Files:**
- Create: `sim/metrics.py`, `scripts/run.py`
- Test: `tests/test_metrics.py`, `tests/test_harness_all_rules.py`, `tests/test_boundary.py`

**Interfaces:**
- Produces: `summarize(res) -> dict` (`sstar, W, gross_eff, net_eff, audit_spend, audit_cost, audited_fraction, value, cost, entry, buyer_surplus, profit_i`); `gain(attack, ref, focal)`; `harm(attack, ref, focal) -> (accounting, direct)`; `scripts/run.py`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_metrics.py
import hashlib, subprocess, sys
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.metrics import summarize, gain, harm
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.twin import Twin
from sim.rng import make_draws


def cfgb(budget, T=60):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def honest(n):
    return [HonestMax() for _ in range(n)]


def test_summary_definitions():
    cfg = cfgb(1.0)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), honest(cfg.N), 0)
    s = summarize(res)
    assert s["gross_eff"] == pytest.approx((res.W + res.audit_cost) / res.sstar)
    assert s["net_eff"] == pytest.approx(res.W / res.sstar)
    assert s["audit_spend"] == pytest.approx(res.audit_cost / res.sstar)
    assert s["audited_fraction"] == pytest.approx(res.audits.sum() / res.served.sum())
    assert "profit_0" in s and "profit_9" in s


def test_full_cheat_on_b1_fixture_has_positive_gain():
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=60, sigma=c.sigma, e=c.e, v_min=0.6, v_max=1.4,
                       providers=c.providers, alpha=c.alpha, budget=0.0)
    rule = PostedPrices(0.20, 0.35, 0.50)
    d = make_draws(cfg, 1); focal = 9
    att = honest(cfg.N); att[focal] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    ref = honest(cfg.N); ref[focal] = Twin(FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0))
    a, b = run_episode(cfg, rule, att, 1, draws=d), run_episode(cfg, rule, ref, 1, draws=d)
    assert gain(a, b, focal) > 0.0


def test_harm_identity_holds():
    cfg = cfgb(1.0)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    d = make_draws(cfg, 2); focal = 7
    att = honest(cfg.N); att[focal] = FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0)
    ref = honest(cfg.N); ref[focal] = Twin(FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0))
    a, b = run_episode(cfg, rule, att, 2, draws=d), run_episode(cfg, rule, ref, 2, draws=d)
    acc, direct = harm(a, b, focal)
    assert acc == pytest.approx(direct, abs=1e-9)


def test_run_script_byte_identical(tmp_path):
    outs = [tmp_path / "a.csv", tmp_path / "b.csv"]
    for out in outs:
        subprocess.run([sys.executable, "scripts/run.py", "--rule", "B2", "--seed", "4", "--budget", "1.0",
                        "--T", "40", "--out", str(out)], check=True)
    assert hashlib.sha256(outs[0].read_bytes()).hexdigest() == hashlib.sha256(outs[1].read_bytes()).hexdigest()
```

```python
# tests/test_harness_all_rules.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.metrics import gain
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.twin import Twin
from sim.rng import make_draws

RULES = [PostedPrices(0.25, 0.40, 0.55), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), SecondScore(tol=0.12, L=10)]
IDS = [r.name for r in RULES]


def tiny(budget=0.5):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=20, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def honest(n):
    return [HonestMax() for _ in range(n)]


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_tiny_market_runs_and_conserves(rule):
    cfg = tiny()
    res = run_episode(cfg, rule, honest(cfg.N), 0)
    assert np.isfinite(res.W) and res.sstar > 0
    res.ledger.check_conservation(0.0)


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_all_honest_mean_gross_efficiency_at_most_one(rule):
    cfg = tiny()
    effs = np.array([(lambda r: (r.W + r.audit_cost) / r.sstar)(run_episode(cfg, rule, honest(cfg.N), s)) for s in range(20)])
    assert effs.mean() <= 1.0 + 2 * effs.std(ddof=1) / np.sqrt(20)
    assert effs.mean() > 0.4


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_honest_max_equals_its_twin_round_by_round(rule):
    cfg = tiny()
    d = make_draws(cfg, 3)
    twins = honest(cfg.N); twins[4] = Twin(HonestMax())
    a, b = run_episode(cfg, rule, honest(cfg.N), 3, draws=d), run_episode(cfg, rule, twins, 3, draws=d)
    assert np.array_equal(a.claims, b.claims, equal_nan=True) and np.array_equal(a.served, b.served)
    assert gain(a, b, focal=4) == 0.0


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_twin_claim_never_exceeds_effort(rule):
    cfg = tiny()
    res = run_episode(cfg, rule, [Twin(FixedCheat(u=0.3, m=0.8, s=0.0, w=0.2, clip=0)) for _ in range(cfg.N)], 1)
    assert np.all(np.nan_to_num(res.claims, nan=-1.0) <= res.efforts + 1e-12)
```

```python
# tests/test_boundary.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.base import Offer
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.base import Action
from sim.policies.honest import HonestMax
from sim.rng import Draws, make_draws


class SameClaimLowEffort:
    name = "same_claim_low_effort"

    def act(self, view):
        p = view.params
        return Action(effort=p.q_max * 0.5, offer=Offer(claim=p.q_max, bid=p.a + p.b * p.q_max))


def cfgb(budget, T=30):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def rule():
    return PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=0)


def test_hidden_effort_does_not_change_decisions_without_audits():
    cfg = cfgb(budget=0.0)
    d = make_draws(cfg, 0)
    a = run_episode(cfg, rule(), [HonestMax() for _ in range(cfg.N)], 0, draws=d)
    b = run_episode(cfg, rule(), [SameClaimLowEffort() for _ in range(cfg.N)], 0, draws=d)
    for ra, rb in zip(a.history, b.history):
        assert ra.assignment == rb.assignment and ra.payments == rb.payments and ra.audits == rb.audits


def test_audit_selection_does_not_depend_on_hidden_effort_or_noise():
    cfg = cfgb(budget=5.0)
    d = make_draws(cfg, 0)
    a = run_episode(cfg, rule(), [HonestMax() for _ in range(cfg.N)], 0, draws=d)
    b = run_episode(cfg, rule(), [SameClaimLowEffort() for _ in range(cfg.N)], 0, draws=d)
    for ra, rb in zip(a.history, b.history):
        assert [r.job for r in ra.audits] == [r.job for r in rb.audits]


def test_relabeling_identities_relabels_decisions():
    cfg = cfgb(budget=1.0)
    d = make_draws(cfg, 5)
    perm = np.array([3, 0, 9, 1, 7, 2, 8, 5, 4, 6])   # new index -> old index
    cfg_p = MarketConfig(N=cfg.N, J=cfg.J, T=cfg.T, sigma=cfg.sigma, e=cfg.e, v_min=cfg.v_min, v_max=cfg.v_max,
                         providers=tuple(cfg.providers[o] for o in perm), alpha=cfg.alpha, budget=cfg.budget)
    d_p = Draws(values=d.values, noise=d.noise[:, perm, :], tie_key=d.tie_key[:, :, perm], audit_u=d.audit_u,
                audit_key=d.audit_key, policy_seed=d.policy_seed[:, perm])
    r = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    a = run_episode(cfg, r, [HonestMax() for _ in range(cfg.N)], 5, draws=d)
    b = run_episode(cfg_p, r, [HonestMax() for _ in range(cfg.N)], 5, draws=d_p)
    inv = np.argsort(perm)   # old index -> new index
    for ra, rb in zip(a.history, b.history):
        assert {j: int(inv[i]) for j, i in ra.assignment.items()} == rb.assignment
    assert np.allclose(a.profit[perm], b.profit)


def test_enforce_output_type_is_checked():
    class WrongType(PostedRandomAudit):
        def enforce(self, records, view):
            return {"refunds": {}}
    cfg = cfgb(budget=5.0)
    with pytest.raises(TypeError):
        run_episode(cfg, WrongType(0.25, 0.40, 0.55, tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_metrics.py tests/test_harness_all_rules.py tests/test_boundary.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.metrics'`

- [ ] **Step 3: Write the implementation**

```python
# sim/metrics.py
from __future__ import annotations

from .market import EpisodeResult


def summarize(res: EpisodeResult) -> dict[str, float]:
    served = int(res.served.sum())
    out = {
        "sstar": res.sstar, "W": res.W,
        "gross_eff": (res.W + res.audit_cost) / res.sstar,
        "net_eff": res.W / res.sstar,
        "audit_spend": res.audit_cost / res.sstar,
        "audit_cost": res.audit_cost,
        "audited_fraction": (int(res.audits.sum()) / served) if served else 0.0,
        "value": res.value, "cost": res.cost, "entry": res.entry, "buyer_surplus": res.buyer_surplus,
    }
    for i in range(len(res.profit)):
        out[f"profit_{i}"] = float(res.profit[i])
    return out


def gain(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> float:
    n = len(attack.profit)
    return float((attack.profit[focal] - ref.profit[focal]) / (attack.sstar / n))


def _others(res: EpisodeResult, focal: int) -> float:
    return res.buyer_surplus + float(res.profit.sum() - res.profit[focal]) - res.audit_cost


def harm(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> tuple[float, float]:
    accounting = ((ref.W - attack.W) + (attack.profit[focal] - ref.profit[focal])) / attack.sstar
    direct = (_others(ref, focal) - _others(attack, focal)) / attack.sstar
    return float(accounting), float(direct)
```

```python
# scripts/run.py
from __future__ import annotations

import argparse, csv, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.metrics import summarize
from sim.policies.honest import HonestMax


def make_rule(name: str):
    return {"B1": lambda: PostedPrices(0.25, 0.40, 0.55),
            "B2": lambda: PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10),
            "B3": lambda: SecondScore(tol=0.12, L=10)}[name]()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", required=True, choices=["B1", "B2", "B3"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--budget", type=float, default=0.0)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=args.T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=args.budget)
    res = run_episode(cfg, make_rule(args.rule), [HonestMax() for _ in range(cfg.N)], args.seed)
    row = {"rule": args.rule, "seed": args.seed, **summarize(res)}
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        w.writeheader()
        w.writerow({k: (f"{v:.12g}" if isinstance(v, float) else v) for k, v in row.items()})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_metrics.py tests/test_harness_all_rules.py tests/test_boundary.py -v`
Expected: PASS (4 + 12 + 4 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/metrics.py scripts/run.py tests/test_metrics.py tests/test_harness_all_rules.py tests/test_boundary.py
git commit -m "feat: metrics, gain and harm, shared harness tests across rules, boundary tests, run script"
```

---

### Task 11: Pilot gate benchmark at a realistic budget

**Files:**
- Create: `scripts/bench.py`
- Test: `tests/test_bench.py`

**Interfaces:**
- Produces: `bench_episode_ms(n_runs=20, warmups=3) -> float`, median ms per `T = 200` B2 episode at `B = 0.05 S_hat`, with draws and `S*` computed once and passed in; the script prints the CPU model and exits 1 above 45 ms.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bench.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_pilot_gate_loose_bound_in_ci():
    from bench import bench_episode_ms
    ms = bench_episode_ms(n_runs=5)
    print(f"median episode time: {ms:.1f} ms")
    assert ms < 400.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bench.py -v -s`
Expected: FAIL with `ModuleNotFoundError: No module named 'bench'`

- [ ] **Step 3: Write the benchmark**

```python
# scripts/bench.py
from __future__ import annotations

import platform, statistics, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.config import MarketConfig
from sim.firstbest import first_best_episode
from sim.market import run_episode
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax
from sim.rng import make_draws

GATE_MS = 45.0


def cpu_model() -> str:
    try:
        if sys.platform == "darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def bench_episode_ms(n_runs: int = 20, warmups: int = 3) -> float:
    c = MarketConfig.default()
    base = MarketConfig(N=c.N, J=c.J, T=200, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=0.0)
    s_hat = statistics.mean(first_best_episode(base, make_draws(base, s)) for s in range(5))
    cfg = MarketConfig(N=c.N, J=c.J, T=200, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=0.05 * s_hat)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    pols = [HonestMax() for _ in range(cfg.N)]
    draws = make_draws(cfg, 0)
    sstar = first_best_episode(cfg, draws)
    for _ in range(warmups):
        run_episode(cfg, rule, pols, 0, draws=draws, sstar=sstar)
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        run_episode(cfg, rule, pols, 0, draws=draws, sstar=sstar)
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times)


if __name__ == "__main__":
    ms = bench_episode_ms()
    print(f"median T=200 B2 episode at B=0.05*S_hat: {ms:.1f} ms (gate {GATE_MS} ms) on {cpu_model()}")
    sys.exit(0 if ms <= GATE_MS else 1)
```

- [ ] **Step 4: Run the suite and the benchmark; optimize only what the profile shows**

Run: `uv run pytest -q && uv run python scripts/bench.py`
Expected: all tests PASS. If the median is above 45 ms, profile with `uv run python -m cProfile -s cumtime scripts/bench.py | head -40`. The expected hot spots are the two `StateView` constructions per round (each copying four arrays) and the ten `ProviderView` constructions. Reduce them by building one `StateView` per round and updating `audits_left` and `escrow` for the audit step through `object.__setattr__`, and by making `ProviderHistory.append` a single tuple append. Re-measure after each change; stop at the first measurement at or below 45 ms. Record the number and the CPU in the commit message. If no change reaches 45 ms on the development machine, record the measured number and leave the gate failing: the gate is a measurement, not something to tune away.

- [ ] **Step 5: Commit**

```bash
git add scripts/bench.py tests/test_bench.py sim/market.py sim/mechanisms/base.py sim/policies/base.py
git commit -m "perf: pilot gate benchmark at 0.05 S_hat (median NN ms on <cpu>)"
```

---

### Task 12: Spec amendments and README status

**Files:**
- Modify: `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (sections 7 and 14), `README.md` (Status)

- [ ] **Step 1: Record the RNG keying and the package path in the spec**

In section 7, replace the paragraph beginning "Common random numbers. Job values and delivery noise are drawn from" through "Action-independent draws and S* are precomputed per seed and shared across cells." with:

```
Common random numbers. Every random input of an episode (job values, delivery
noise, allocation tie-break keys, the audit-count rounding uniform, audit
priority keys, and policy seeds) is a pure function of (seed, t), drawn in a
fixed order from one `numpy.random.SeedSequence([seed, t])` child and laid
out in fixed positions (job index; provider index and slot index). No action
can change any draw; `tests/test_rng.py`, `tests/test_market.py`,
`tests/test_posted_audit.py`, and `tests/test_boundary.py` check it. One
child per round instead of one per job costs nothing in the per-run gate
(draws are shared across cells) and saves about 117 core-hours in the
coverage study. S* is computed once per seed and passed to every run on that
seed.
```

Append to section 14:

```
Implementation (plan 1, core engine, version 2 after two reviews): draws
keyed per (seed, round) with fixed intra-round layout; operator randomness
precomputed per job and per round so audit counts and selections are
action-independent; a read-only StateView for rules with the harness
validating every rule output against section 4.0; audit outcomes recorded by
the harness from the rule's declared tolerance; integer audit allowance;
bonds, forfeits, and releases in the ledger before the lock; package path
`sim/` as in section 11.
```

- [ ] **Step 2: Update the README status**

Replace the README's `## Status` body with:

```
Week 1. Core engine implemented: market with a validated rule interface,
ledger with bonds, first-best, B1 to B3, honest-max and fixed-cheat policies
with the truthful twin, metrics, run script, and the pilot benchmark. Plan 2
(search, families, manifest, calibration, tuning, coverage study, claim
script, model actors, identity replacement) next.
```

- [ ] **Step 3: Run the whole suite**

Run: `uv run pytest -q`
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md README.md
git commit -m "docs: record RNG keying, harness validation, and package path in the spec"
```

---

## Self-review

**Spec coverage for this plan's scope.** Section 3: Tasks 2 (both validity conditions), 7 (round sequence, observations, claim semantics via twin and records), 8 (integer allowance). Section 4 interface and 4.0 class: Task 4 (types, read-only view, five methods including `describe()`), Task 5 (ledger applies every consequence type, forced release at the cap), Task 6 (every output validated, consequences tied to failed records). Section 4.1 B1, B2, B3: Tasks 7, 8, 9, with the worked example, the three caps, action-independent selection, and `describe()` records. Sections 5.1 to 5.3 (D1, clip knob, domains): Task 7. Section 7: Tasks 3, 5, 10, with per-round ledger arrays, conservation every round, audited fraction. Section 12 tests in scope: honest-max equals its twin under every rule; all-honest mean gross efficiency under every rule; one-provider closed form; byte-identical CSV; allowance never exceeded, per-round cap, exact last-round rounding; schedule expectation and hypergeometric criterion; B1 fixture positive gain; deviation leaves draws unchanged; cash conservation each round and harm identity on a bond-capable ledger; interface rejects an effort field and a rule cannot write state; identical visible histories with different hidden effort or noise give identical decisions; relabeling; enforce output type; honest failure rate; S* > 0; twin never exceeds effort; shared tiny-market test per mechanism with the B3 worked example. Not in this plan, by the stated split: search checks, locked-config and sealed-bundle hashes, `describe()` rendering, LLM replay, coverage study, ablation.

**Placeholder scan.** None. Task 11 names the exact hot spots and the stopping rule.

**Type consistency.** `Offer(claim, bid)`; `Consequences(refunds, bans, holdbacks, forfeits, releases)`; `AuditRecord(job, provider, delivered, claim, failed)`; `StateView(...)` with `memory["tie_key"]` set by the harness before `allocate`; `Mechanism.allocate(values_t, offers, view)`, `price(assignment, values_t, offers, view)`, `audit(assignment, view)`, `enforce(records, view)`, `describe()`, `bind(cfg)`; `run_episode(cfg, rule, policies, seed, draws=None, sstar=None)`; `gain(attack, ref, focal)`, `harm(attack, ref, focal)`; `Ledger.settle(t, escrow, owner, cons, failed_jobs_of)`.

**Review Focus.** Items 1, 2, 5: Task 8. Item 3: Tasks 3 and 7. Item 4: Task 7. Item 6: Tasks 6, 7, and 10.
