# Touchstone core engine implementation plan (plan 1 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the claimed-quality market simulator with its ledger, first-best benchmark, the three tuned-later baselines B1 to B3, honest-max and fixed-cheat policies with the truthful-twin wrapper, the core metrics, and a timed pilot that runs one 200-round B2 episode in under 45 ms.

**Architecture:** A pure-Python package `touchstone` with NumPy for per-round vector work. Random draws are precomputed per seed and keyed by round so no action can change a later draw. A `Mechanism` sees offers only and returns consequences; a `Ledger` owns every economic field. Policies see their own view only. One `run_episode` function wires them together and returns a result object that `metrics` summarizes.

**Tech Stack:** Python 3.13, numpy, scipy (linear_sum_assignment, stats), pytest. Package and dependency management with `uv`. No other runtime dependency in this plan.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5). This plan implements sections 3, 4 (interface, admissible class, B1 to B3), 5.1, 5.2 (honest-max and the twin wrapper), 5.3 (D1 only), 7 (S*, ledger, W, efficiency, gain, harm), 12 (the tests those sections name), and the first gate of section 13. Plan 2 (search, D2, manifest, calibration, tuning, coverage study, check_claim, LLM and Jev actors, H3) and plan 3 (post-freeze evaluation) follow.

**Scope split, stated once:** Plan 1 stops at the pilot gate of 2026-10-17. It does not contain CMA-ES, D2, the candidate bank, the coverage study, `describe()` rendering, bond forfeit schedules, identity replacement, or any proposed rule. Bond hold-backs are accepted by the ledger and released at the end of the episode; forfeit schedules arrive with the proposed rule in plan 3.

## Global Constraints

- Jobs are unit jobs: every job has size 1 (spec 3).
- Delivered quality is `effort + eps`, `eps ~ N(0, sigma^2)`, never clipped (spec 3).
- Claim semantics: a claim is truthful iff `claim <= effort` (spec 3).
- The operator never sees effort or unaudited delivery; `Mechanism` methods receive offers only (spec 3, 4.0).
- Admissible consequences only: refund up to the job's escrowed payment; ban at most `L_MAX = 50` rounds; hold-back at most `H_MAX = 3` rounds of net released receipts; no fees, no consequences for unaudited jobs (spec 4.0).
- The operator injects no money; its net position is audit cost only (spec 4.0, 7).
- Audit spend never exceeds the budget `B` in any seed; audits are integer (spec 3, 4.1).
- Common random numbers: job values, delivery noise, and operator and policy randomness are precomputed per seed and keyed by round, independent of any action (spec 7, with the keying noted in Task 2).
- First-best `S*` is the exact maximum-weight assignment of unit jobs to capacity slots at full effort, with weight `max(0, v_j * q_max_i - a_i - b_i * q_max_i)` (spec 7).
- Same config and seed give a byte-identical CSV (spec 12).
- Pilot gate: one `T = 200` B2 episode under 45 ms on one core (spec 13).
- Python package name `touchstone`, tests under `tests/`, scripts under `scripts/` (spec 11).
- Configuration validity: for every provider `v_min * q_max_i - a_i - b_i * q_max_i > 0` (spec 3).

## Review Focus

Inputs the spec implies but no section names. Each line has its test pinned to the owning task.

1. Every provider banned in some round, so no eligible offer exists: every job stays unserved that round, `W` and efficiency are still computed, nothing raises. Pinned to Task 7.
2. Remaining budget below one audit's cost (`budget_left < alpha`): zero audits that round, no negative budget, the spread schedule's cap logic does not divide by zero in round `T`. Pinned to Task 7.
3. A provider whose capacity exceeds the number of jobs (`k_i > J`): the slot matrix for `S*` and the allocation loops handle it without index errors. Pinned to Task 3 and Task 6.
4. Two jobs with identical values: the descending sort is stable and deterministic, so the same seed gives the same assignment. Pinned to Task 6.
5. Negative delivered quality from noise (`effort + eps < 0`): buyer value is negative for that job, the audit failure test still compares `y < claim - tol`, and no code clips or rejects it. Pinned to Task 7.

---

### Task 1: Package scaffold and test harness

**Files:**
- Create: `pyproject.toml`
- Create: `touchstone/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_scaffold.py`
- Modify: `.gitignore` (append `.venv/`, `*.egg-info/`, `.pytest_cache/`, `uv.lock` stays tracked)

**Interfaces:**
- Produces: importable package `touchstone` with `__version__ = "0.1.0"`; `uv run pytest` works.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scaffold.py
def test_package_imports():
    import touchstone
    assert touchstone.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest tests/test_scaffold.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone'`

- [ ] **Step 3: Write the scaffold**

```toml
# pyproject.toml
[project]
name = "touchstone"
version = "0.1.0"
description = "Audit-and-allocation rules for markets of adaptive agents: simulator"
requires-python = ">=3.12"
dependencies = [
    "numpy>=2.0",
    "scipy>=1.13",
]

[dependency-groups]
dev = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["touchstone"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
# touchstone/__init__.py
__version__ = "0.1.0"
```

```python
# tests/__init__.py
```

Append to `.gitignore`:

```
.venv/
*.egg-info/
.pytest_cache/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv sync && uv run pytest tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock touchstone/__init__.py tests/__init__.py tests/test_scaffold.py .gitignore
git commit -m "feat: package scaffold and test harness"
```

---

### Task 2: Configuration, validity check, and keyed random draws

**Files:**
- Create: `touchstone/config.py`
- Create: `touchstone/rng.py`
- Test: `tests/test_config.py`, `tests/test_rng.py`

**Interfaces:**
- Produces:
  - `ProviderParams(q_max: float, a: float, b: float, k: int)` frozen dataclass.
  - `MarketConfig(N, J, T, sigma, e, v_min, v_max, providers: tuple[ProviderParams, ...], alpha: float, budget: float)` frozen dataclass with `validate() -> None` (raises `ValueError`) and classmethod `default() -> MarketConfig`.
  - `Draws(values: np.ndarray[T, J], noise: np.ndarray[T, N, kmax], op_seed: np.ndarray[T], policy_seed: np.ndarray[T, N])`.
  - `make_draws(cfg: MarketConfig, seed: int) -> Draws`.

**Spec note to record in the spec at commit time (section 7, common random numbers):** draws are keyed by `(seed, round)` and laid out in fixed positions within the round (job index, provider index and slot index), rather than by one `SeedSequence` child per job. The property the spec wants, that no action changes any later draw, holds exactly and is tested below; per-job children would cost about 100 ms per episode and break the pilot gate.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config.py
import pytest
from touchstone.config import MarketConfig, ProviderParams


def test_default_config_is_valid():
    cfg = MarketConfig.default()
    cfg.validate()
    assert cfg.N == 10 and cfg.J == 50 and cfg.T == 200
    assert len(cfg.providers) == cfg.N


def test_validity_rejects_unprofitable_provider():
    base = MarketConfig.default()
    bad = ProviderParams(q_max=0.5, a=0.5, b=0.5, k=5)
    cfg = MarketConfig(
        N=base.N, J=base.J, T=base.T, sigma=base.sigma, e=base.e,
        v_min=base.v_min, v_max=base.v_max,
        providers=base.providers[:-1] + (bad,),
        alpha=base.alpha, budget=base.budget,
    )
    with pytest.raises(ValueError, match="first-best weight"):
        cfg.validate()


def test_validity_rejects_zero_capacity():
    base = MarketConfig.default()
    bad = ProviderParams(q_max=0.9, a=0.02, b=0.3, k=0)
    cfg = MarketConfig(
        N=base.N, J=base.J, T=base.T, sigma=base.sigma, e=base.e,
        v_min=base.v_min, v_max=base.v_max,
        providers=base.providers[:-1] + (bad,),
        alpha=base.alpha, budget=base.budget,
    )
    with pytest.raises(ValueError, match="capacity"):
        cfg.validate()
```

```python
# tests/test_rng.py
import numpy as np
from touchstone.config import MarketConfig
from touchstone.rng import make_draws


def test_draw_shapes_and_ranges():
    cfg = MarketConfig.default()
    d = make_draws(cfg, seed=7)
    kmax = max(p.k for p in cfg.providers)
    assert d.values.shape == (cfg.T, cfg.J)
    assert d.noise.shape == (cfg.T, cfg.N, kmax)
    assert d.op_seed.shape == (cfg.T,)
    assert d.policy_seed.shape == (cfg.T, cfg.N)
    assert d.values.min() >= cfg.v_min and d.values.max() <= cfg.v_max
    assert abs(d.noise.std() - cfg.sigma) < 0.01


def test_same_seed_same_draws():
    cfg = MarketConfig.default()
    a = make_draws(cfg, seed=3)
    b = make_draws(cfg, seed=3)
    assert np.array_equal(a.values, b.values)
    assert np.array_equal(a.noise, b.noise)
    assert np.array_equal(a.op_seed, b.op_seed)
    assert np.array_equal(a.policy_seed, b.policy_seed)


def test_different_seed_different_draws():
    cfg = MarketConfig.default()
    a = make_draws(cfg, seed=3)
    b = make_draws(cfg, seed=4)
    assert not np.array_equal(a.values, b.values)


def test_round_t_draws_do_not_depend_on_t_minus_1():
    # The draws for round t are a pure function of (seed, t): generating only
    # round t must equal row t of the full generation.
    from touchstone.rng import draws_for_round
    cfg = MarketConfig.default()
    full = make_draws(cfg, seed=11)
    for t in (0, 1, 57, cfg.T - 1):
        v, n, o, p = draws_for_round(cfg, seed=11, t=t)
        assert np.array_equal(v, full.values[t])
        assert np.array_equal(n, full.noise[t])
        assert o == full.op_seed[t]
        assert np.array_equal(p, full.policy_seed[t])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py tests/test_rng.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.config'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/config.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderParams:
    q_max: float   # quality ceiling, in (0, 1]
    a: float       # fixed cost per job served
    b: float       # cost per unit of effort per job served
    k: int         # capacity, jobs per round


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
    alpha: float    # audit cost per audited job
    budget: float   # total audit budget B over the episode

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
                raise ValueError(
                    f"provider {i}: first-best weight at v_min is {weight:.4f}, must be > 0"
                )

    @property
    def kmax(self) -> int:
        return max(p.k for p in self.providers)

    @classmethod
    def default(cls) -> "MarketConfig":
        # Ten heterogeneous providers; every one satisfies the validity condition
        # at v_min = 0.6 (worst case: q_max 0.6, b 0.40: 0.36 - 0.02 - 0.24 = 0.10).
        q_max = [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.00]
        b = [0.40, 0.38, 0.36, 0.34, 0.32, 0.30, 0.28, 0.26, 0.24, 0.22]
        providers = tuple(
            ProviderParams(q_max=q, a=0.02, b=bb, k=6) for q, bb in zip(q_max, b)
        )
        return cls(
            N=10, J=50, T=200, sigma=0.05, e=0.0, v_min=0.6, v_max=1.4,
            providers=providers, alpha=0.05, budget=0.0,
        )
```

```python
# touchstone/rng.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import MarketConfig


@dataclass(frozen=True)
class Draws:
    values: np.ndarray        # (T, J) job values
    noise: np.ndarray         # (T, N, kmax) delivery noise per provider slot
    op_seed: np.ndarray       # (T,) operator randomness seed per round
    policy_seed: np.ndarray   # (T, N) policy randomness seed per round and provider


def _round_rng(seed: int, t: int) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([int(seed), int(t)]))


def draws_for_round(cfg: MarketConfig, seed: int, t: int):
    """Draws for one round as a pure function of (seed, t). Fixed draw order:
    values, noise, operator seed, policy seeds."""
    g = _round_rng(seed, t)
    values = g.uniform(cfg.v_min, cfg.v_max, size=cfg.J)
    noise = g.normal(0.0, cfg.sigma, size=(cfg.N, cfg.kmax))
    op_seed = int(g.integers(0, 2**31 - 1))
    policy_seed = g.integers(0, 2**31 - 1, size=cfg.N)
    return values, noise, op_seed, policy_seed


def make_draws(cfg: MarketConfig, seed: int) -> Draws:
    values = np.empty((cfg.T, cfg.J))
    noise = np.empty((cfg.T, cfg.N, cfg.kmax))
    op_seed = np.empty(cfg.T, dtype=np.int64)
    policy_seed = np.empty((cfg.T, cfg.N), dtype=np.int64)
    for t in range(cfg.T):
        v, n, o, p = draws_for_round(cfg, seed, t)
        values[t] = v
        noise[t] = n
        op_seed[t] = o
        policy_seed[t] = p
    return Draws(values=values, noise=noise, op_seed=op_seed, policy_seed=policy_seed)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py tests/test_rng.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add touchstone/config.py touchstone/rng.py tests/test_config.py tests/test_rng.py
git commit -m "feat: market config with validity check and round-keyed draws"
```

---

### Task 3: First-best benchmark S*

**Files:**
- Create: `touchstone/firstbest.py`
- Test: `tests/test_firstbest.py`

**Interfaces:**
- Consumes: `MarketConfig`, `Draws` from Task 2.
- Produces:
  - `pair_weights(cfg) -> np.ndarray[N]`: per-provider weight coefficient at full effort, `q_max_i` and `a_i + b_i q_max_i`, exposed as `(q_full: np.ndarray[N], cost_full: np.ndarray[N])` via `full_effort_terms(cfg)`.
  - `first_best_round(cfg, values_t: np.ndarray[J]) -> float`.
  - `first_best_episode(cfg, draws) -> float` (sum over rounds).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_firstbest.py
import numpy as np
import pytest
from touchstone.config import MarketConfig, ProviderParams
from touchstone.firstbest import first_best_round, first_best_episode
from touchstone.rng import make_draws


def one_provider_cfg(q_max=0.8, a=0.1, b=0.5, k=1, J=1, v=1.0):
    return MarketConfig(
        N=1, J=J, T=1, sigma=0.0, e=0.0, v_min=v, v_max=v,
        providers=(ProviderParams(q_max=q_max, a=a, b=b, k=k),),
        alpha=0.0, budget=0.0,
    )


def test_one_provider_one_job_closed_form():
    cfg = one_provider_cfg()
    # weight = v*q_max - a - b*q_max = 0.8 - 0.1 - 0.4 = 0.3
    assert first_best_round(cfg, np.array([1.0])) == pytest.approx(0.3)


def test_capacity_exceeds_jobs_is_fine():
    cfg = one_provider_cfg(k=7, J=2)
    # two jobs, both served at weight 0.3 each
    assert first_best_round(cfg, np.array([1.0, 1.0])) == pytest.approx(0.6)


def test_jobs_exceed_capacity_picks_highest_values():
    cfg = MarketConfig(
        N=1, J=3, T=1, sigma=0.0, e=0.0, v_min=0.6, v_max=2.0,
        providers=(ProviderParams(q_max=1.0, a=0.0, b=0.5, k=2),),
        alpha=0.0, budget=0.0,
    )
    # weights: v*1 - 0.5 -> 1.5, 0.5, 0.1 ; best two = 2.0
    assert first_best_round(cfg, np.array([2.0, 1.0, 0.6])) == pytest.approx(2.0)


def test_episode_is_positive_and_sums_rounds():
    cfg = MarketConfig.default()
    d = make_draws(cfg, seed=1)
    total = first_best_episode(cfg, d)
    per_round = sum(first_best_round(cfg, d.values[t]) for t in range(cfg.T))
    assert total == pytest.approx(per_round)
    assert total > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_firstbest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.firstbest'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/firstbest.py
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from .config import MarketConfig
from .rng import Draws


def full_effort_terms(cfg: MarketConfig) -> tuple[np.ndarray, np.ndarray]:
    q_full = np.array([p.q_max for p in cfg.providers])
    cost_full = np.array([p.a + p.b * p.q_max for p in cfg.providers])
    return q_full, cost_full


def _slot_owner(cfg: MarketConfig) -> np.ndarray:
    return np.repeat(np.arange(cfg.N), [p.k for p in cfg.providers])


def first_best_round(cfg: MarketConfig, values_t: np.ndarray) -> float:
    """Exact maximum-weight assignment of unit jobs to capacity slots at full
    effort. Weight of (provider i, job j) = max(0, v_j q_max_i - a_i - b_i q_max_i).
    Zero-weight pairs mean 'do not serve' and add nothing."""
    q_full, cost_full = full_effort_terms(cfg)
    owner = _slot_owner(cfg)                                  # (slots,)
    w = values_t[None, :] * q_full[owner][:, None] - cost_full[owner][:, None]
    w = np.maximum(w, 0.0)                                    # (slots, J)
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
git add touchstone/firstbest.py tests/test_firstbest.py
git commit -m "feat: exact first-best benchmark via maximum-weight assignment"
```

---

### Task 4: Offer, consequence, and mechanism types with admissible-class validation

**Files:**
- Create: `touchstone/types.py`
- Create: `touchstone/mechanisms/__init__.py`
- Create: `touchstone/mechanisms/base.py`
- Test: `tests/test_admissible.py`

**Interfaces:**
- Produces:
  - `Offer(claim: float, bid: float)` frozen dataclass. `Offers = dict[int, Offer]` keyed by provider index; absence means abstain.
  - `Assignment = dict[int, int]` job index to provider index. `Payments = dict[int, float]` job index to payment.
  - `AuditResult(job: int, provider: int, delivered: float, claim: float)`.
  - `Consequences(refunds: dict[int, float], bans: dict[int, int], holdbacks: dict[int, float])`, keys job, identity, identity.
  - `L_MAX = 50`, `H_MAX = 3`.
  - `class Mechanism` with abstract `allocate(self, values_t, offers, state, op_rng) -> Assignment`, `price(self, assignment, values_t, offers, state) -> Payments`, `audit(self, assignment, state, budget_left, op_rng) -> list[int]`, `enforce(self, results: list[AuditResult], state) -> tuple[Consequences, dict]`, and `name: str`.
  - `validate_consequences(cons, escrow: dict[int, float], recent_receipts: dict[int, float]) -> None` raising `ValueError` on any violation of spec 4.0.
  - `OfferError` raised by `Offer.__post_init__` if a caller passes an `effort` field (information boundary test).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_admissible.py
import pytest
from touchstone.types import Offer, Consequences, L_MAX, H_MAX
from touchstone.mechanisms.base import validate_consequences


def test_offer_has_no_effort_field():
    with pytest.raises(TypeError):
        Offer(claim=0.8, bid=0.3, effort=0.7)  # type: ignore[call-arg]


def test_offer_claim_in_unit_interval():
    with pytest.raises(ValueError):
        Offer(claim=1.2, bid=0.3)
    with pytest.raises(ValueError):
        Offer(claim=-0.1, bid=0.3)


def test_refund_cannot_exceed_escrow():
    cons = Consequences(refunds={3: 0.9}, bans={}, holdbacks={})
    with pytest.raises(ValueError, match="refund"):
        validate_consequences(cons, escrow={3: 0.5}, recent_receipts={})


def test_refund_on_job_without_escrow_rejected():
    cons = Consequences(refunds={9: 0.1}, bans={}, holdbacks={})
    with pytest.raises(ValueError, match="escrow"):
        validate_consequences(cons, escrow={3: 0.5}, recent_receipts={})


def test_ban_bounded_by_l_max():
    ok = Consequences(refunds={}, bans={0: L_MAX}, holdbacks={})
    validate_consequences(ok, escrow={}, recent_receipts={})
    bad = Consequences(refunds={}, bans={0: L_MAX + 1}, holdbacks={})
    with pytest.raises(ValueError, match="ban"):
        validate_consequences(bad, escrow={}, recent_receipts={})


def test_holdback_bounded_by_recent_receipts():
    ok = Consequences(refunds={}, bans={}, holdbacks={2: 1.0})
    validate_consequences(ok, escrow={}, recent_receipts={2: 1.0})
    bad = Consequences(refunds={}, bans={}, holdbacks={2: 1.5})
    with pytest.raises(ValueError, match="hold-back"):
        validate_consequences(bad, escrow={}, recent_receipts={2: 1.0})


def test_negative_amounts_rejected():
    with pytest.raises(ValueError):
        validate_consequences(Consequences(refunds={1: -0.1}, bans={}, holdbacks={}),
                              escrow={1: 0.5}, recent_receipts={})
    with pytest.raises(ValueError):
        validate_consequences(Consequences(refunds={}, bans={1: -2}, holdbacks={}),
                              escrow={}, recent_receipts={})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_admissible.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.types'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/types.py
from __future__ import annotations

from dataclasses import dataclass, field

L_MAX = 50   # longest admissible ban, in rounds (spec 4.0)
H_MAX = 3    # most rounds of net released receipts a rule may hold back (spec 4.0)


@dataclass(frozen=True)
class Offer:
    """A provider's public offer. Effort is private and is never part of it."""
    claim: float
    bid: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.claim <= 1.0):
            raise ValueError("claim must be in [0, 1]")
        if self.bid < 0.0:
            raise ValueError("bid must be non-negative")


Offers = dict[int, Offer]          # provider index -> offer; missing = abstain
Assignment = dict[int, int]        # job index -> provider index
Payments = dict[int, float]        # job index -> payment funded by the buyer


@dataclass(frozen=True)
class AuditResult:
    job: int
    provider: int
    delivered: float
    claim: float


@dataclass
class Consequences:
    """Everything a rule may impose. Validated against spec 4.0 before the
    ledger applies it."""
    refunds: dict[int, float] = field(default_factory=dict)     # job -> amount
    bans: dict[int, int] = field(default_factory=dict)          # identity -> rounds
    holdbacks: dict[int, float] = field(default_factory=dict)   # identity -> amount
```

```python
# touchstone/mechanisms/__init__.py
```

```python
# touchstone/mechanisms/base.py
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..types import Assignment, AuditResult, Consequences, H_MAX, L_MAX, Offers, Payments


def validate_consequences(
    cons: Consequences,
    escrow: dict[int, float],
    recent_receipts: dict[int, float],
) -> None:
    """Raise ValueError if the consequences leave the admissible class (spec 4.0).
    escrow: job -> escrowed payment this round.
    recent_receipts: identity -> net released receipts over the last H_MAX rounds."""
    for job, amount in cons.refunds.items():
        if amount < 0:
            raise ValueError(f"refund for job {job} is negative")
        if job not in escrow:
            raise ValueError(f"refund for job {job} without escrow")
        if amount > escrow[job] + 1e-12:
            raise ValueError(f"refund for job {job} exceeds its escrow")
    for ident, rounds in cons.bans.items():
        if rounds < 0:
            raise ValueError(f"ban for identity {ident} is negative")
        if rounds > L_MAX:
            raise ValueError(f"ban for identity {ident} exceeds L_MAX={L_MAX}")
    for ident, amount in cons.holdbacks.items():
        if amount < 0:
            raise ValueError(f"hold-back for identity {ident} is negative")
        cap = recent_receipts.get(ident, 0.0)
        if amount > cap + 1e-12:
            raise ValueError(
                f"hold-back for identity {ident} exceeds {H_MAX} rounds of receipts"
            )


class Mechanism(ABC):
    """A market rule. It sees offers, job values, audit results, and its own
    state; never effort or unaudited delivery. It returns consequences; the
    ledger applies them."""

    name: str = "mechanism"

    @abstractmethod
    def allocate(self, values_t: np.ndarray, offers: Offers, state, op_rng: np.random.Generator) -> Assignment: ...

    @abstractmethod
    def price(self, assignment: Assignment, values_t: np.ndarray, offers: Offers, state) -> Payments: ...

    @abstractmethod
    def audit(self, assignment: Assignment, state, budget_left: float, op_rng: np.random.Generator) -> list[int]: ...

    @abstractmethod
    def enforce(self, results: list[AuditResult], state) -> tuple[Consequences, dict]: ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_admissible.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add touchstone/types.py touchstone/mechanisms/__init__.py touchstone/mechanisms/base.py tests/test_admissible.py
git commit -m "feat: offer and consequence types, mechanism interface, admissible-class validation"
```

---

### Task 5: Operator state and ledger with cash conservation

**Files:**
- Create: `touchstone/state.py`
- Create: `touchstone/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: `Consequences`, `validate_consequences` from Task 4.
- Produces:
  - `OperatorState(N: int, T: int, budget: float)` with economic fields `banned_until: np.ndarray[N] (int, round index until which the identity cannot offer, exclusive)`, `budget_left: float`, `bond: np.ndarray[N]`, `t: int`, and `memory: dict` for rule policy memory. `is_active(i) -> bool`.
  - `Ledger(N)` with per-identity cumulative arrays `funding, refunds, receipts, holdback_in, holdback_out, cost, entry` and methods:
    - `fund(job, provider, amount)` (buyer money into escrow),
    - `charge_cost(provider, amount)`, `charge_entry(provider, amount)`,
    - `apply(cons: Consequences, state, escrow: dict[int, float], job_owner: dict[int, int], t: int)` which validates, books refunds and hold-backs, sets bans, and returns nothing,
    - `settle_round(escrow, job_owner, refunds_this_round: dict[int, float], holdbacks_this_round: dict[int, float])` which releases remaining escrow to providers,
    - `terminal_settlement(state)` releasing all outstanding bonds at the end,
    - `profit() -> np.ndarray[N]` = receipts + holdback_out − cost − entry (refunds already excluded from receipts),
    - `check_conservation(escrow_outstanding: float)` asserting `funding == receipts + refunds + bond_outstanding + escrow_outstanding` to 1e-9.
    - `recent_receipts(window: int) -> dict[int, float]` summing the last `window` rounds of net released receipts per identity (used for the hold-back cap).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ledger.py
import numpy as np
import pytest
from touchstone.ledger import Ledger
from touchstone.state import OperatorState
from touchstone.types import Consequences


def test_fund_then_settle_releases_to_provider():
    led = Ledger(N=2)
    st = OperatorState(N=2, T=5, budget=0.0)
    escrow, owner = {}, {}
    led.fund(job=0, provider=1, amount=0.7, escrow=escrow, owner=owner)
    led.settle_round(escrow, owner, refunds={}, holdbacks={})
    assert led.receipts[1] == pytest.approx(0.7)
    assert led.funding[1] == pytest.approx(0.7)
    led.check_conservation(escrow_outstanding=0.0)
    assert led.profit()[1] == pytest.approx(0.7)


def test_refund_goes_back_to_buyer_and_reduces_receipts():
    led = Ledger(N=1)
    st = OperatorState(N=1, T=5, budget=0.0)
    escrow, owner = {}, {}
    led.fund(0, 0, 1.0, escrow, owner)
    cons = Consequences(refunds={0: 1.0}, bans={0: 3}, holdbacks={})
    led.apply(cons, st, escrow, owner, t=2)
    led.settle_round(escrow, owner, refunds=cons.refunds, holdbacks=cons.holdbacks)
    assert led.refunds[0] == pytest.approx(1.0)
    assert led.receipts[0] == pytest.approx(0.0)
    assert st.banned_until[0] == 2 + 3 + 1   # banned for rounds 3, 4, 5
    assert not st.is_active(0, t=5) and st.is_active(0, t=6)
    led.check_conservation(escrow_outstanding=0.0)


def test_holdback_is_bond_until_terminal_settlement():
    led = Ledger(N=1)
    st = OperatorState(N=1, T=5, budget=0.0)
    escrow, owner = {}, {}
    led.fund(0, 0, 1.0, escrow, owner)
    led.settle_round(escrow, owner, refunds={}, holdbacks={})
    # next round: rule holds back 0.4 of recent receipts
    led.fund(1, 0, 1.0, escrow, owner)
    cons = Consequences(refunds={}, bans={}, holdbacks={0: 0.4})
    led.apply(cons, st, escrow, owner, t=1)
    led.settle_round(escrow, owner, refunds={}, holdbacks=cons.holdbacks)
    assert st.bond[0] == pytest.approx(0.4)
    assert led.receipts[0] == pytest.approx(1.6)
    led.check_conservation(escrow_outstanding=0.0)
    led.terminal_settlement(st)
    assert st.bond[0] == pytest.approx(0.0)
    assert led.profit()[0] == pytest.approx(2.0)
    led.check_conservation(escrow_outstanding=0.0)


def test_apply_rejects_inadmissible():
    led = Ledger(N=1)
    st = OperatorState(N=1, T=5, budget=0.0)
    escrow, owner = {}, {}
    led.fund(0, 0, 0.5, escrow, owner)
    with pytest.raises(ValueError):
        led.apply(Consequences(refunds={0: 0.9}, bans={}, holdbacks={}), st, escrow, owner, t=0)


def test_cost_and_entry_reduce_profit():
    led = Ledger(N=1)
    led.charge_cost(0, 0.3)
    led.charge_entry(0, 0.1)
    assert led.profit()[0] == pytest.approx(-0.4)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.ledger'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/state.py
from __future__ import annotations

import numpy as np


class OperatorState:
    """Operator memory. Economic fields are written only by the Ledger; a rule
    reads them and writes only `memory`."""

    def __init__(self, N: int, T: int, budget: float) -> None:
        self.N = N
        self.T = T
        self.budget_left = float(budget)
        self.banned_until = np.zeros(N, dtype=np.int64)   # round index, exclusive
        self.bond = np.zeros(N)                            # outstanding hold-backs
        self.t = 0
        self.memory: dict = {}

    def is_active(self, i: int, t: int | None = None) -> bool:
        tt = self.t if t is None else t
        return tt >= int(self.banned_until[i])
```

```python
# touchstone/ledger.py
from __future__ import annotations

import numpy as np

from .mechanisms.base import validate_consequences
from .state import OperatorState
from .types import Consequences, H_MAX


class Ledger:
    """Owns every money flow. Buyers fund escrow; the ledger refunds, holds
    back, and releases. Conservation: funding = receipts + refunds +
    outstanding bond + outstanding escrow, at every point."""

    def __init__(self, N: int) -> None:
        self.N = N
        self.funding = np.zeros(N)
        self.refunds = np.zeros(N)
        self.receipts = np.zeros(N)        # net released receipts, cumulative
        self.holdback_in = np.zeros(N)     # amounts moved into bond
        self.holdback_out = np.zeros(N)    # amounts released from bond
        self.cost = np.zeros(N)
        self.entry = np.zeros(N)
        self.audit_cost = 0.0
        self._receipts_by_round: list[np.ndarray] = []
        self._bond = None  # bound to state.bond at apply time

    # --- money in ---
    def fund(self, job: int, provider: int, amount: float, escrow: dict, owner: dict) -> None:
        if amount < 0:
            raise ValueError("payment must be non-negative")
        escrow[job] = escrow.get(job, 0.0) + amount
        owner[job] = provider
        self.funding[provider] += amount

    def charge_cost(self, provider: int, amount: float) -> None:
        self.cost[provider] += amount

    def charge_entry(self, provider: int, amount: float) -> None:
        self.entry[provider] += amount

    def charge_audit(self, amount: float) -> None:
        self.audit_cost += amount

    # --- consequences ---
    def recent_receipts(self, window: int = H_MAX) -> dict[int, float]:
        if not self._receipts_by_round:
            return {i: 0.0 for i in range(self.N)}
        recent = np.sum(self._receipts_by_round[-window:], axis=0)
        return {i: float(recent[i]) for i in range(self.N)}

    def apply(self, cons: Consequences, state: OperatorState, escrow: dict, owner: dict, t: int) -> None:
        validate_consequences(cons, escrow, self.recent_receipts())
        for ident, rounds in cons.bans.items():
            if rounds > 0:
                state.banned_until[ident] = max(int(state.banned_until[ident]), t + rounds + 1)
        self._bond = state.bond

    def settle_round(self, escrow: dict, owner: dict, refunds: dict, holdbacks: dict) -> None:
        released = np.zeros(self.N)
        for job, amount in list(escrow.items()):
            provider = owner[job]
            refund = min(refunds.get(job, 0.0), amount)
            self.refunds[provider] += refund
            released[provider] += amount - refund
        for ident, amount in holdbacks.items():
            take = min(amount, released[ident])
            released[ident] -= take
            self.holdback_in[ident] += take
            if self._bond is not None:
                self._bond[ident] += take
        self.receipts += released
        self._receipts_by_round.append(released)
        escrow.clear()
        owner.clear()

    def terminal_settlement(self, state: OperatorState) -> None:
        self.holdback_out += state.bond
        state.bond[:] = 0.0

    # --- accounting ---
    def profit(self) -> np.ndarray:
        return self.receipts + self.holdback_out - self.cost - self.entry

    def check_conservation(self, escrow_outstanding: float, bond_outstanding: float | None = None) -> None:
        bond = (self._bond.sum() if self._bond is not None else 0.0) if bond_outstanding is None else bond_outstanding
        lhs = self.funding.sum()
        rhs = self.receipts.sum() + self.refunds.sum() + self.holdback_out.sum() + bond + escrow_outstanding
        if abs(lhs - rhs) > 1e-9:
            raise AssertionError(f"cash not conserved: funding {lhs:.9f} vs {rhs:.9f}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ledger.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add touchstone/state.py touchstone/ledger.py tests/test_ledger.py
git commit -m "feat: operator state and ledger with cash conservation"
```

---

### Task 6: Policies (honest-max, fixed cheat, twin), B1 posted prices, and the episode loop

**Files:**
- Create: `touchstone/policies/__init__.py`
- Create: `touchstone/policies/base.py`
- Create: `touchstone/policies/honest.py`
- Create: `touchstone/policies/fixed_cheat.py`
- Create: `touchstone/policies/twin.py`
- Create: `touchstone/mechanisms/posted.py`
- Create: `touchstone/market.py`
- Test: `tests/test_policies.py`, `tests/test_posted.py`, `tests/test_market.py`

**Interfaces:**
- Consumes: Tasks 2 to 5.
- Produces:
  - `ProviderView(i, params: ProviderParams, t, posted_prices: tuple[float, ...] | None, history: ProviderHistory, rng: np.random.Generator)`; `ProviderHistory` has lists `served`, `payments`, `audited`, `failed` per round and `banned_until: int`.
  - `Action(effort: float, offer: Offer | None, exit: bool = False)`.
  - `Policy` protocol: `act(view: ProviderView) -> Action`; attribute `name`.
  - `HonestMax()`; `FixedCheat(u, m, s, w, clip)` per spec 5.3 D1; `Twin(policy)` wrapper that clips `offer.claim` to `min(claim, effort)`.
  - `PostedPrices(P1, P2, P3)` (B1) with `TIERS = ((0.0, 0.5), (0.5, 0.8), (0.8, 1.0001))` and `tier_of(claim) -> int`.
  - `EpisodeResult` dataclass: `sstar: float`, `profit: np.ndarray[N]`, `value: float` (sum v*y), `cost: float`, `entry: float`, `audit_cost: float`, `served: np.ndarray[T, N]` counts, `audits: np.ndarray[T]` counts, `failures: np.ndarray[T, N]`, `claims: np.ndarray[T, N]` (NaN when abstaining), `efforts: np.ndarray[T, N]`, `buyer_surplus: float` (value − funding + refunds), `W: float` (value − cost − entry − audit_cost).
  - `run_episode(cfg, rule, policies: list[Policy], seed: int, draws: Draws | None = None) -> EpisodeResult`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_policies.py
import numpy as np
import pytest
from touchstone.config import MarketConfig
from touchstone.policies.base import ProviderView, ProviderHistory
from touchstone.policies.honest import HonestMax
from touchstone.policies.fixed_cheat import FixedCheat
from touchstone.policies.twin import Twin


def view(i=0, t=0):
    cfg = MarketConfig.default()
    return ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=None,
                        history=ProviderHistory(), rng=np.random.default_rng(0))


def test_honest_max_claims_effort_bids_cost():
    a = HonestMax().act(view(i=3))
    p = MarketConfig.default().providers[3]
    assert a.effort == pytest.approx(p.q_max)
    assert a.offer.claim == pytest.approx(p.q_max)
    assert a.offer.bid == pytest.approx(p.a + p.b * p.q_max)
    assert a.exit is False


def test_fixed_cheat_knobs():
    p = MarketConfig.default().providers[0]   # q_max 0.6
    a = FixedCheat(u=0.5, m=0.4, s=0.1, w=0.5, clip=0).act(view(i=0))
    assert a.effort == pytest.approx(0.3)
    assert a.offer.claim == pytest.approx(min(1.0, max(0.0, 0.3 + 0.4 - 0.1)))
    assert a.offer.bid == pytest.approx(1.5 * (p.a + p.b * 0.3))


def test_fixed_cheat_with_clip_never_inflates():
    a = FixedCheat(u=0.5, m=0.9, s=0.0, w=0.0, clip=1).act(view(i=0))
    assert a.offer.claim <= a.effort + 1e-12


def test_twin_clips_claim_to_effort():
    base = FixedCheat(u=0.0, m=1.0, s=0.0, w=0.0, clip=0)
    raw = base.act(view(i=0))
    assert raw.offer.claim > raw.effort
    tw = Twin(base).act(view(i=0))
    assert tw.effort == pytest.approx(raw.effort)
    assert tw.offer.claim == pytest.approx(raw.effort)
    assert tw.offer.bid == pytest.approx(raw.offer.bid)


def test_honest_max_equals_its_twin():
    for i in range(10):
        a = HonestMax().act(view(i=i))
        b = Twin(HonestMax()).act(view(i=i))
        assert a == b
```

```python
# tests/test_posted.py
import numpy as np
import pytest
from touchstone.mechanisms.posted import PostedPrices
from touchstone.state import OperatorState
from touchstone.types import Offer


def test_tier_boundaries():
    r = PostedPrices(P1=0.2, P2=0.4, P3=0.6)
    assert r.tier_of(0.0) == 0 and r.tier_of(0.49) == 0
    assert r.tier_of(0.5) == 1 and r.tier_of(0.79) == 1
    assert r.tier_of(0.8) == 2 and r.tier_of(1.0) == 2


def test_allocation_prefers_highest_tier_and_respects_acceptance():
    r = PostedPrices(P1=0.2, P2=0.4, P3=0.6)
    st = OperatorState(N=2, T=1, budget=0.0)
    st.capacity_left = np.array([1, 1])
    # job value 0.7: tier-3 claim 0.9 -> 0.63 >= 0.6 accepted; tier-1 claim 0.4 -> 0.28 >= 0.2 accepted
    offers = {0: Offer(claim=0.4, bid=0.0), 1: Offer(claim=0.9, bid=0.0)}
    asg = r.allocate(np.array([0.7]), offers, st, op_rng=np.random.default_rng(0))
    assert asg == {0: 1}
    pay = r.price(asg, np.array([0.7]), offers, st)
    assert pay == {0: pytest.approx(0.6)}


def test_job_with_no_acceptable_tier_stays_unserved():
    r = PostedPrices(P1=0.5, P2=0.7, P3=0.9)
    st = OperatorState(N=1, T=1, budget=0.0)
    st.capacity_left = np.array([1])
    offers = {0: Offer(claim=0.6, bid=0.0)}   # tier 2 price 0.7; value 0.6*0.6=0.36 < 0.7
    asg = r.allocate(np.array([0.6]), offers, st, op_rng=np.random.default_rng(0))
    assert asg == {}


def test_banned_provider_is_not_eligible():
    r = PostedPrices(P1=0.2, P2=0.4, P3=0.6)
    st = OperatorState(N=1, T=5, budget=0.0)
    st.t = 2
    st.banned_until[0] = 4
    st.capacity_left = np.array([1])
    offers = {0: Offer(claim=0.9, bid=0.0)}
    asg = r.allocate(np.array([1.0]), offers, st, op_rng=np.random.default_rng(0))
    assert asg == {}
```

```python
# tests/test_market.py
import numpy as np
import pytest
from touchstone.config import MarketConfig, ProviderParams
from touchstone.market import run_episode
from touchstone.mechanisms.posted import PostedPrices
from touchstone.policies.honest import HonestMax
from touchstone.policies.fixed_cheat import FixedCheat
from touchstone.rng import make_draws


def b1():
    return PostedPrices(P1=0.25, P2=0.40, P3=0.55)


def test_all_honest_efficiency_at_most_one_plus_noise():
    cfg = MarketConfig.default()
    effs = []
    for seed in range(20):
        res = run_episode(cfg, b1(), [HonestMax() for _ in range(cfg.N)], seed)
        effs.append((res.W + res.audit_cost) / res.sstar)
    effs = np.array(effs)
    assert effs.mean() <= 1.0 + 2 * effs.std(ddof=1) / np.sqrt(len(effs))
    assert effs.mean() > 0.5


def test_same_seed_same_result():
    cfg = MarketConfig.default()
    pols = [HonestMax() for _ in range(cfg.N)]
    a = run_episode(cfg, b1(), pols, seed=5)
    b = run_episode(cfg, b1(), pols, seed=5)
    assert a.W == b.W and np.array_equal(a.profit, b.profit)
    assert np.array_equal(a.claims, b.claims, equal_nan=True)


def test_deviation_in_round_t_leaves_round_t_plus_one_draws_unchanged():
    cfg = MarketConfig.default()
    d1 = make_draws(cfg, seed=9)
    pols = [HonestMax() for _ in range(cfg.N)]
    pols_dev = [HonestMax() for _ in range(cfg.N)]
    pols_dev[0] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    a = run_episode(cfg, b1(), pols, seed=9, draws=d1)
    b = run_episode(cfg, b1(), pols_dev, seed=9, draws=d1)
    # draws are shared and action-independent; the deviator changes outcomes, not draws
    assert a.draws_id == b.draws_id
    assert not np.array_equal(a.profit, b.profit)


def test_capacity_above_jobs_runs():
    cfg0 = MarketConfig.default()
    big = tuple(ProviderParams(p.q_max, p.a, p.b, k=80) for p in cfg0.providers)
    cfg = MarketConfig(N=10, J=50, T=3, sigma=0.05, e=0.0, v_min=0.6, v_max=1.4,
                       providers=big, alpha=0.05, budget=0.0)
    res = run_episode(cfg, b1(), [HonestMax() for _ in range(10)], seed=1)
    assert res.served.sum() <= 3 * 50


def test_tied_values_are_deterministic():
    cfg0 = MarketConfig.default()
    cfg = MarketConfig(N=10, J=50, T=5, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0,
                       providers=cfg0.providers, alpha=0.05, budget=0.0)
    pols = [HonestMax() for _ in range(10)]
    a = run_episode(cfg, b1(), pols, seed=2)
    b = run_episode(cfg, b1(), pols, seed=2)
    assert np.array_equal(a.served, b.served)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_policies.py tests/test_posted.py tests/test_market.py -v`
Expected: FAIL with `ModuleNotFoundError` on `touchstone.policies`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/policies/__init__.py
```

```python
# touchstone/policies/base.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from ..config import ProviderParams
from ..types import Offer


@dataclass
class ProviderHistory:
    """What a provider has seen about itself. Appended once per round."""
    served: list[int] = field(default_factory=list)
    payments: list[float] = field(default_factory=list)
    audited: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)
    banned_until: int = 0


@dataclass(frozen=True)
class ProviderView:
    i: int
    params: ProviderParams
    t: int
    posted_prices: tuple[float, ...] | None
    history: ProviderHistory
    rng: np.random.Generator


@dataclass(frozen=True)
class Action:
    effort: float
    offer: Offer | None       # None = abstain
    exit: bool = False


class Policy(Protocol):
    name: str

    def act(self, view: ProviderView) -> Action: ...
```

```python
# touchstone/policies/honest.py
from __future__ import annotations

from ..types import Offer
from .base import Action, ProviderView


class HonestMax:
    """Full effort, claim equal to effort, bid equal to cost (spec 5.2)."""
    name = "honest_max"

    def act(self, view: ProviderView) -> Action:
        p = view.params
        q = p.q_max
        return Action(effort=q, offer=Offer(claim=q, bid=p.a + p.b * q), exit=False)
```

```python
# touchstone/policies/fixed_cheat.py
from __future__ import annotations

from ..types import Offer
from .base import Action, ProviderView


class FixedCheat:
    """D1 (spec 5.3). effort = q_max (1 - u); claim = min(1, max(0, effort + m - s));
    bid = (1 + w) cost(effort); clip = 1 projects the claim to <= effort."""
    name = "fixed_cheat"

    def __init__(self, u: float, m: float, s: float, w: float, clip: int) -> None:
        self.u, self.m, self.s, self.w, self.clip = float(u), float(m), float(s), float(w), int(clip)

    def act(self, view: ProviderView) -> Action:
        p = view.params
        effort = p.q_max * (1.0 - self.u)
        claim = min(1.0, max(0.0, effort + self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        bid = (1.0 + self.w) * (p.a + p.b * effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=bid), exit=False)
```

```python
# touchstone/policies/twin.py
from __future__ import annotations

from ..types import Offer
from .base import Action, ProviderView


class Twin:
    """The truthful twin: same policy, market-facing claim clipped to <= effort
    by the harness (spec 5.2)."""

    def __init__(self, policy) -> None:
        self.policy = policy
        self.name = f"twin({getattr(policy, 'name', 'policy')})"

    def act(self, view: ProviderView) -> Action:
        a = self.policy.act(view)
        if a.offer is None:
            return a
        return Action(effort=a.effort,
                      offer=Offer(claim=min(a.offer.claim, a.effort), bid=a.offer.bid),
                      exit=a.exit)
```

```python
# touchstone/mechanisms/posted.py
from __future__ import annotations

import numpy as np

from ..types import Assignment, AuditResult, Consequences, Offers, Payments
from .base import Mechanism

TIERS = ((0.0, 0.5), (0.5, 0.8), (0.8, 1.0001))


class PostedPrices(Mechanism):
    """B1 (spec 4.1): three price tiers by claim; jobs in descending value;
    each job to a random eligible provider in the highest tier that has one;
    no audits."""
    name = "B1_posted"

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

    def allocate(self, values_t: np.ndarray, offers: Offers, state, op_rng: np.random.Generator) -> Assignment:
        cap = state.capacity_left
        providers = [i for i in offers if state.is_active(i) and cap[i] > 0]
        tiers = {i: self.tier_of(offers[i].claim) for i in providers}
        order = np.argsort(-values_t, kind="stable")
        assignment: Assignment = {}
        for j in order:
            v = values_t[j]
            chosen = -1
            for tier in (2, 1, 0):
                price = self.prices[tier]
                elig = [i for i in providers if tiers[i] == tier and cap[i] > 0
                        and v * offers[i].claim >= price]
                if elig:
                    chosen = int(elig[op_rng.integers(len(elig))])
                    break
            if chosen >= 0:
                assignment[int(j)] = chosen
                cap[chosen] -= 1
        return assignment

    def price(self, assignment: Assignment, values_t: np.ndarray, offers: Offers, state) -> Payments:
        return {j: self.prices[self.tier_of(offers[i].claim)] for j, i in assignment.items()}

    def audit(self, assignment: Assignment, state, budget_left: float, op_rng: np.random.Generator) -> list[int]:
        return []

    def enforce(self, results: list[AuditResult], state) -> tuple[Consequences, dict]:
        return Consequences(), {}
```

```python
# touchstone/market.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import MarketConfig
from .firstbest import first_best_episode
from .ledger import Ledger
from .policies.base import ProviderHistory, ProviderView
from .rng import Draws, make_draws
from .state import OperatorState
from .types import AuditResult, Offer


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
    draws_id: int


def run_episode(cfg: MarketConfig, rule, policies, seed: int, draws: Draws | None = None) -> EpisodeResult:
    cfg.validate()
    if len(policies) != cfg.N:
        raise ValueError("one policy per provider")
    d = draws if draws is not None else make_draws(cfg, seed)
    sstar = first_best_episode(cfg, d)
    state = OperatorState(cfg.N, cfg.T, cfg.budget)
    ledger = Ledger(cfg.N)
    histories = [ProviderHistory() for _ in range(cfg.N)]
    caps = np.array([p.k for p in cfg.providers])
    posted = getattr(rule, "prices", None)

    served = np.zeros((cfg.T, cfg.N), dtype=np.int64)
    audits = np.zeros(cfg.T, dtype=np.int64)
    failures = np.zeros((cfg.T, cfg.N), dtype=np.int64)
    claims = np.full((cfg.T, cfg.N), np.nan)
    efforts = np.zeros((cfg.T, cfg.N))
    value_total = 0.0

    for t in range(cfg.T):
        state.t = t
        values_t = d.values[t]
        op_rng = np.random.default_rng(int(d.op_seed[t]))

        # 2. private effort and public offers
        offers: dict[int, Offer] = {}
        effort = np.zeros(cfg.N)
        for i in range(cfg.N):
            if not state.is_active(i):
                continue
            view = ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=posted,
                                history=histories[i],
                                rng=np.random.default_rng(int(d.policy_seed[t, i])))
            act = policies[i].act(view)
            effort[i] = act.effort
            efforts[t, i] = act.effort
            if act.offer is not None:
                offers[i] = act.offer
                claims[t, i] = act.offer.claim

        # 3. allocate, 4. price into escrow
        state.capacity_left = caps.copy()
        assignment = rule.allocate(values_t, offers, state, op_rng)
        payments = rule.price(assignment, values_t, offers, state)
        escrow: dict[int, float] = {}
        owner: dict[int, int] = {}
        for j, i in assignment.items():
            ledger.fund(j, i, payments[j], escrow, owner)

        # 5. delivery
        slot_used = np.zeros(cfg.N, dtype=np.int64)
        delivered: dict[int, float] = {}
        for j, i in assignment.items():
            y = effort[i] + d.noise[t, i, slot_used[i]]
            slot_used[i] += 1
            delivered[j] = y
            value_total += values_t[j] * y
            ledger.charge_cost(i, cfg.providers[i].a + cfg.providers[i].b * effort[i])
            served[t, i] += 1

        # 6. audit within budget
        to_audit = rule.audit(assignment, state, state.budget_left, op_rng)
        n_aff = min(len(to_audit), int(np.floor(state.budget_left / cfg.alpha + 1e-12)) if cfg.alpha > 0 else len(to_audit))
        to_audit = to_audit[:n_aff]
        results = [AuditResult(job=j, provider=assignment[j], delivered=delivered[j],
                               claim=offers[assignment[j]].claim) for j in to_audit]
        spend = cfg.alpha * len(results)
        state.budget_left -= spend
        ledger.charge_audit(spend)
        audits[t] = len(results)

        # 7. enforce, 8. settle
        cons, memory = rule.enforce(results, state)
        state.memory.update(memory)
        ledger.apply(cons, state, escrow, owner, t)
        for j in cons.refunds:
            failures[t, owner[j]] += 1
        ledger.settle_round(escrow, owner, cons.refunds, cons.holdbacks)

        # provider histories
        for i in range(cfg.N):
            histories[i].served.append(int(served[t, i]))
            histories[i].payments.append(float(sum(payments[j] for j, ii in assignment.items() if ii == i)))
            histories[i].audited.append(int(sum(1 for r in results if r.provider == i)))
            histories[i].failed.append(int(failures[t, i]))
            histories[i].banned_until = int(state.banned_until[i])

    ledger.terminal_settlement(state)
    ledger.check_conservation(escrow_outstanding=0.0, bond_outstanding=0.0)
    cost = float(ledger.cost.sum())
    entry = float(ledger.entry.sum())
    W = value_total - cost - entry - ledger.audit_cost
    buyer_surplus = value_total - float(ledger.funding.sum()) + float(ledger.refunds.sum())
    return EpisodeResult(
        sstar=sstar, profit=ledger.profit(), value=value_total, cost=cost, entry=entry,
        audit_cost=ledger.audit_cost, served=served, audits=audits, failures=failures,
        claims=claims, efforts=efforts, buyer_surplus=buyer_surplus, W=W, draws_id=id(d),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_policies.py tests/test_posted.py tests/test_market.py -v`
Expected: PASS (14 tests)

- [ ] **Step 5: Commit**

```bash
git add touchstone/policies touchstone/mechanisms/posted.py touchstone/market.py tests/test_policies.py tests/test_posted.py tests/test_market.py
git commit -m "feat: policies, B1 posted prices, and the episode loop"
```

---

### Task 7: B2 posted prices with spread random audits

**Files:**
- Create: `touchstone/mechanisms/audit_random.py`
- Create: `touchstone/mechanisms/posted_audit.py`
- Test: `tests/test_posted_audit.py`

**Interfaces:**
- Consumes: `PostedPrices` from Task 6, `Consequences`, `OperatorState`.
- Produces:
  - `spread_audit_count(budget_left, alpha, t, T, served_count, B, op_rng) -> int` implementing spec 4.1: stochastic rounding of `(budget_left/alpha)/(T-t)` (zero-based `t`, so `T - t` rounds remain), capped by served jobs, by `max(1, floor(2B/(T alpha)))`, and by `floor(budget_left/alpha)`.
  - `RandomAuditMixin` with `audit(...)` choosing that many served jobs uniformly, and `enforce(...)` returning a full refund of each failed job and a ban of `L` rounds for its identity; `tol` and `L` attributes.
  - `PostedRandomAudit(P1, P2, P3, tol, L)` (B2) = `PostedPrices` allocation and pricing plus the mixin.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_posted_audit.py
import numpy as np
import pytest
from scipy import stats
from touchstone.config import MarketConfig
from touchstone.market import run_episode
from touchstone.mechanisms.audit_random import spread_audit_count
from touchstone.mechanisms.posted_audit import PostedRandomAudit
from touchstone.policies.honest import HonestMax
from touchstone.rng import make_draws


def b2(tol=0.12, L=10):
    return PostedRandomAudit(P1=0.25, P2=0.40, P3=0.55, tol=tol, L=L)


def cfg_with_budget(budget, T=200):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def test_spread_count_expectation_before_caps():
    rng = np.random.default_rng(0)
    counts = [spread_audit_count(budget_left=100.0, alpha=1.0, t=0, T=8, served_count=1000,
                                 B=100.0, op_rng=rng) for _ in range(20000)]
    assert np.mean(counts) == pytest.approx(100.0 / 8, rel=0.02)


def test_spread_count_hard_caps():
    rng = np.random.default_rng(0)
    # remaining budget below one audit -> zero
    assert spread_audit_count(0.5, 1.0, 5, 10, 50, 100.0, rng) == 0
    # last round: fractional remaining budget never rounds up past floor
    for _ in range(200):
        assert spread_audit_count(1.5, 1.0, 9, 10, 50, 100.0, rng) <= 1
    # per-round cap max(1, floor(2B/(T alpha)))
    for _ in range(200):
        assert spread_audit_count(1000.0, 1.0, 0, 10, 50, 2.0, rng) <= 1
    # served cap
    assert spread_audit_count(1000.0, 1.0, 0, 1, 3, 1000.0, rng) <= 3


def test_total_audit_spend_never_exceeds_budget():
    cfg = cfg_with_budget(budget=3.0)
    for seed in range(5):
        res = run_episode(cfg, b2(), [HonestMax() for _ in range(cfg.N)], seed)
        assert res.audit_cost <= cfg.budget + 1e-9
        assert res.audits.max() <= max(1, int(np.floor(2 * cfg.budget / (cfg.T * cfg.alpha))))


def test_honest_failure_rate_matches_formula():
    # P(y < claim - tol) for honest (claim = effort) = Phi(-tol/sigma)
    cfg = cfg_with_budget(budget=40.0, T=100)   # many audits
    tol = 0.08
    fails, auds = 0, 0
    for seed in range(6):
        res = run_episode(cfg, b2(tol=tol, L=0), [HonestMax() for _ in range(cfg.N)], seed)
        fails += res.failures.sum()
        auds += res.audits.sum()
    p_hat = fails / auds
    p = stats.norm.cdf(-tol / cfg.sigma)
    se = np.sqrt(p * (1 - p) / auds)
    assert abs(p_hat - p) < 4 * se + 0.005


def test_spread_halves_balanced_statistically():
    cfg = cfg_with_budget(budget=2.0)   # 40 audits expected: 20 per half
    diffs = []
    for seed in range(200):
        res = run_episode(cfg, b2(L=0), [HonestMax() for _ in range(cfg.N)], seed)
        h = cfg.T // 2
        diffs.append(abs(res.audits[:h].sum() - res.audits[h:].sum()))
    # expected |diff| for 40 draws split 50/50 ~ sqrt(2*40*0.25)*sqrt(2/pi)*2 ~ 3.6; allow generous band
    assert np.mean(diffs) < 8.0


def test_all_providers_banned_round_is_fine():
    cfg = cfg_with_budget(budget=50.0, T=30)
    rule = b2(tol=-10.0, L=20)   # every audited job fails -> bans pile up
    res = run_episode(cfg, rule, [HonestMax() for _ in range(cfg.N)], seed=0)
    assert np.isfinite(res.W)
    assert (res.served.sum(axis=1) == 0).any()


def test_negative_delivery_is_valued_and_audited_without_clipping():
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=20, sigma=0.9, e=0.0, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=20.0)
    res = run_episode(cfg, b2(tol=0.0, L=0), [HonestMax() for _ in range(cfg.N)], seed=0)
    assert np.isfinite(res.value)
    assert res.failures.sum() > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_posted_audit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.mechanisms.audit_random'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/mechanisms/audit_random.py
from __future__ import annotations

import numpy as np

from ..types import Assignment, AuditResult, Consequences


def spread_audit_count(budget_left: float, alpha: float, t: int, T: int,
                       served_count: int, B: float, op_rng: np.random.Generator) -> int:
    """Spec 4.1 spread schedule. t is zero-based, so T - t rounds remain."""
    if alpha <= 0 or budget_left < alpha:
        return 0
    target = (budget_left / alpha) / (T - t)
    base = int(np.floor(target))
    frac = target - base
    n = base + (1 if op_rng.random() < frac else 0)
    n = min(n, int(served_count))
    n = min(n, max(1, int(np.floor(2.0 * B / (T * alpha)))))
    n = min(n, int(np.floor(budget_left / alpha + 1e-12)))
    return max(0, n)


class RandomAuditMixin:
    """Uniform random audits on the spread schedule; failed audit refunds the
    job's payment and bans the identity L rounds (spec 4.1 B2/B3)."""
    tol: float
    L: int
    B: float
    alpha: float
    T: int

    def audit(self, assignment: Assignment, state, budget_left: float, op_rng: np.random.Generator) -> list[int]:
        jobs = list(assignment.keys())
        n = spread_audit_count(budget_left, self.alpha, state.t, self.T, len(jobs), self.B, op_rng)
        if n == 0:
            return []
        pick = op_rng.choice(len(jobs), size=n, replace=False)
        return [jobs[k] for k in pick]

    def enforce(self, results: list[AuditResult], state) -> tuple[Consequences, dict]:
        cons = Consequences()
        for r in results:
            if r.delivered < r.claim - self.tol:
                cons.refunds[r.job] = float(state.escrow_of[r.job])
                if self.L > 0:
                    cons.bans[r.provider] = max(cons.bans.get(r.provider, 0), self.L)
        return cons, {}
```

```python
# touchstone/mechanisms/posted_audit.py
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
        self.B = 0.0
        self.alpha = 0.0
        self.T = 1

    def bind(self, cfg) -> None:
        """Called by run_episode so the schedule knows B, alpha, T."""
        self.B = float(cfg.budget)
        self.alpha = float(cfg.alpha)
        self.T = int(cfg.T)
```

Modify `touchstone/market.py` in two places. First, right after `state = OperatorState(...)`:

```python
    if hasattr(rule, "bind"):
        rule.bind(cfg)
```

Second, inside the round loop just before `to_audit = rule.audit(...)`, expose the escrow map read-only to the rule and read the mixin's attributes from the state rather than the rule:

```python
        state.escrow_of = dict(escrow)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_posted_audit.py tests/test_market.py -v`
Expected: PASS (7 new tests, earlier tests still green)

- [ ] **Step 5: Commit**

```bash
git add touchstone/mechanisms/audit_random.py touchstone/mechanisms/posted_audit.py touchstone/market.py tests/test_posted_audit.py
git commit -m "feat: B2 posted prices with spread random audits and enforcement"
```

---

### Task 8: B3 second-score sequential auction

**Files:**
- Create: `touchstone/mechanisms/second_score.py`
- Test: `tests/test_second_score.py`

**Interfaces:**
- Consumes: `RandomAuditMixin` from Task 7.
- Produces: `SecondScore(tol, L)` (B3): jobs in descending value; eligible = active, capacity left, score `v*claim - bid >= 0`; winner max score, ties random via `op_rng`; payment `v*claim_w - s2` (`s2` = second-highest eligible score, or 0).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_second_score.py
import numpy as np
import pytest
from touchstone.config import MarketConfig
from touchstone.market import run_episode
from touchstone.mechanisms.second_score import SecondScore
from touchstone.policies.honest import HonestMax
from touchstone.state import OperatorState
from touchstone.types import Offer


def test_worked_example_payment_is_three():
    r = SecondScore(tol=0.12, L=10)
    st = OperatorState(N=2, T=1, budget=0.0)
    st.capacity_left = np.array([1, 1])
    offers = {0: Offer(claim=1.0, bid=1.0), 1: Offer(claim=1.0, bid=3.0)}
    asg = r.allocate(np.array([10.0]), offers, st, op_rng=np.random.default_rng(0))
    assert asg == {0: 0}
    pay = r.price(asg, np.array([10.0]), offers, st)
    assert pay[0] == pytest.approx(3.0)


def test_single_eligible_bidder_pays_its_score_equivalent():
    r = SecondScore(tol=0.12, L=10)
    st = OperatorState(N=1, T=1, budget=0.0)
    st.capacity_left = np.array([1])
    offers = {0: Offer(claim=0.9, bid=0.5)}
    asg = r.allocate(np.array([2.0]), offers, st, op_rng=np.random.default_rng(0))
    pay = r.price(asg, np.array([2.0]), offers, st)
    assert pay[0] == pytest.approx(2.0 * 0.9 - 0.0)


def test_negative_score_not_eligible():
    r = SecondScore(tol=0.12, L=10)
    st = OperatorState(N=1, T=1, budget=0.0)
    st.capacity_left = np.array([1])
    offers = {0: Offer(claim=0.5, bid=1.0)}   # 0.6*0.5 - 1 < 0
    asg = r.allocate(np.array([0.6]), offers, st, op_rng=np.random.default_rng(0))
    assert asg == {}


def test_capacity_respected_in_sequence():
    r = SecondScore(tol=0.12, L=10)
    st = OperatorState(N=2, T=1, budget=0.0)
    st.capacity_left = np.array([1, 5])
    offers = {0: Offer(claim=1.0, bid=0.1), 1: Offer(claim=1.0, bid=0.5)}
    asg = r.allocate(np.array([1.0, 1.0, 1.0]), offers, st, op_rng=np.random.default_rng(0))
    assert sum(1 for i in asg.values() if i == 0) == 1
    assert sum(1 for i in asg.values() if i == 1) == 2


def test_full_episode_runs_with_audits():
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=50, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=2.0)
    res = run_episode(cfg, SecondScore(tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], seed=0)
    assert res.audit_cost <= cfg.budget + 1e-9
    assert res.W > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_second_score.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.mechanisms.second_score'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/mechanisms/second_score.py
from __future__ import annotations

import numpy as np

from ..types import Assignment, Offers, Payments
from .audit_random import RandomAuditMixin
from .base import Mechanism


class SecondScore(RandomAuditMixin, Mechanism):
    """B3 (spec 4.1): sequential second-score auction with capacity, random
    audits as in B2. Not truthful; the paper never calls it VCG."""
    name = "B3_second_score"

    def __init__(self, tol: float, L: int) -> None:
        self.tol = float(tol)
        self.L = int(L)
        self.B, self.alpha, self.T = 0.0, 0.0, 1

    def bind(self, cfg) -> None:
        self.B, self.alpha, self.T = float(cfg.budget), float(cfg.alpha), int(cfg.T)

    def allocate(self, values_t: np.ndarray, offers: Offers, state, op_rng: np.random.Generator) -> Assignment:
        cap = state.capacity_left
        order = np.argsort(-values_t, kind="stable")
        assignment: Assignment = {}
        state.memory.setdefault("second_scores", {})
        s2_map: dict[int, float] = {}
        for j in order:
            v = values_t[j]
            scored = []
            for i, off in offers.items():
                if not state.is_active(i) or cap[i] <= 0:
                    continue
                s = v * off.claim - off.bid
                if s >= 0:
                    scored.append((s, i))
            if not scored:
                continue
            top = max(s for s, _ in scored)
            winners = [i for s, i in scored if s == top]
            w = int(winners[op_rng.integers(len(winners))]) if len(winners) > 1 else winners[0]
            rest = [s for s, i in scored if i != w]
            s2 = max(rest) if rest else 0.0
            assignment[int(j)] = w
            s2_map[int(j)] = float(s2)
            cap[w] -= 1
        state.memory["second_scores"] = s2_map
        return assignment

    def price(self, assignment: Assignment, values_t: np.ndarray, offers: Offers, state) -> Payments:
        s2 = state.memory.get("second_scores", {})
        return {j: float(values_t[j] * offers[i].claim - s2.get(j, 0.0)) for j, i in assignment.items()}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_second_score.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add touchstone/mechanisms/second_score.py tests/test_second_score.py
git commit -m "feat: B3 second-score sequential auction with random audits"
```

---

### Task 9: Metrics, gain against a reference run, harm identity, and the run script

**Files:**
- Create: `touchstone/metrics.py`
- Create: `scripts/run.py`
- Test: `tests/test_metrics.py`

**Interfaces:**
- Consumes: `EpisodeResult`, `run_episode`, policies, rules.
- Produces:
  - `summarize(res: EpisodeResult) -> dict[str, float]` with keys `sstar, W, gross_eff, net_eff, audit_spend, audit_cost, value, cost, entry, buyer_surplus` and `profit_{i}` per provider.
  - `gain(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> float` = `(attack.profit[focal] - ref.profit[focal]) / (attack.sstar / N)`.
  - `harm(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> tuple[float, float]`: `(accounting, direct)` where accounting = `[(W_ref - W_attack) + (pi_attack - pi_ref)] / S*` and direct = change in summed utility of buyers, non-focal providers, and the operator, over `S*`. The test asserts they agree.
  - `scripts/run.py --rule {B1,B2,B3} --seed N --out file.csv` writing one row of `summarize` plus provider profits; byte-identical for the same args.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_metrics.py
import subprocess, sys, hashlib
import numpy as np
import pytest
from touchstone.config import MarketConfig
from touchstone.market import run_episode
from touchstone.mechanisms.posted import PostedPrices
from touchstone.mechanisms.posted_audit import PostedRandomAudit
from touchstone.metrics import summarize, gain, harm
from touchstone.policies.honest import HonestMax
from touchstone.policies.fixed_cheat import FixedCheat
from touchstone.policies.twin import Twin
from touchstone.rng import make_draws


def cfg_b(budget):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=60, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def test_summary_keys_and_efficiency_definitions():
    cfg = cfg_b(1.0)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10),
                      [HonestMax() for _ in range(cfg.N)], seed=0)
    s = summarize(res)
    assert s["gross_eff"] == pytest.approx((res.W + res.audit_cost) / res.sstar)
    assert s["net_eff"] == pytest.approx(res.W / res.sstar)
    assert s["audit_spend"] == pytest.approx(res.audit_cost / res.sstar)
    assert "profit_0" in s and "profit_9" in s


def test_honest_max_gain_against_its_twin_is_zero():
    cfg = cfg_b(1.0)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    d = make_draws(cfg, seed=3)
    pols = [HonestMax() for _ in range(cfg.N)]
    twins = [HonestMax() for _ in range(cfg.N)]
    twins[4] = Twin(HonestMax())
    a = run_episode(cfg, rule, pols, 3, draws=d)
    b = run_episode(cfg, rule, twins, 3, draws=d)
    assert gain(a, b, focal=4) == 0.0


def test_full_cheat_on_b1_fixture_has_positive_gain():
    # fixture: every job accepts tier 3 (v_min * 1.0 >= P3) and P3 > a
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=60, sigma=c.sigma, e=c.e, v_min=0.6, v_max=1.4,
                       providers=c.providers, alpha=c.alpha, budget=0.0)
    rule = PostedPrices(0.20, 0.35, 0.50)
    d = make_draws(cfg, seed=1)
    focal = 9
    attack = [HonestMax() for _ in range(cfg.N)]
    attack[focal] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    twin = [HonestMax() for _ in range(cfg.N)]
    twin[focal] = Twin(FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0))
    a = run_episode(cfg, rule, attack, 1, draws=d)
    b = run_episode(cfg, rule, twin, 1, draws=d)
    assert gain(a, b, focal) > 0.0


def test_harm_identity_holds():
    cfg = cfg_b(1.0)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    d = make_draws(cfg, seed=2)
    focal = 7
    attack = [HonestMax() for _ in range(cfg.N)]
    attack[focal] = FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0)
    ref = [HonestMax() for _ in range(cfg.N)]
    ref[focal] = Twin(FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0))
    a = run_episode(cfg, rule, attack, 2, draws=d)
    b = run_episode(cfg, rule, ref, 2, draws=d)
    accounting, direct = harm(a, b, focal)
    assert accounting == pytest.approx(direct, abs=1e-9)


def test_run_script_is_byte_identical(tmp_path):
    out1, out2 = tmp_path / "a.csv", tmp_path / "b.csv"
    for out in (out1, out2):
        subprocess.run([sys.executable, "scripts/run.py", "--rule", "B2", "--seed", "4",
                        "--budget", "1.0", "--T", "40", "--out", str(out)], check=True)
    assert hashlib.sha256(out1.read_bytes()).hexdigest() == hashlib.sha256(out2.read_bytes()).hexdigest()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'touchstone.metrics'`

- [ ] **Step 3: Write the implementation**

```python
# touchstone/metrics.py
from __future__ import annotations

from .market import EpisodeResult


def summarize(res: EpisodeResult) -> dict[str, float]:
    n = len(res.profit)
    out = {
        "sstar": res.sstar,
        "W": res.W,
        "gross_eff": (res.W + res.audit_cost) / res.sstar,
        "net_eff": res.W / res.sstar,
        "audit_spend": res.audit_cost / res.sstar,
        "audit_cost": res.audit_cost,
        "value": res.value,
        "cost": res.cost,
        "entry": res.entry,
        "buyer_surplus": res.buyer_surplus,
    }
    for i in range(n):
        out[f"profit_{i}"] = float(res.profit[i])
    return out


def gain(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> float:
    """Spec 7: (pi_attack - pi_ref) / (S* / N), same seeds."""
    n = len(attack.profit)
    return float((attack.profit[focal] - ref.profit[focal]) / (attack.sstar / n))


def _others_utility(res: EpisodeResult, focal: int) -> float:
    others = float(res.profit.sum() - res.profit[focal])
    operator = -res.audit_cost
    return res.buyer_surplus + others + operator


def harm(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> tuple[float, float]:
    """Spec 7 harm to others. Returns (accounting identity, direct computation),
    both in units of S*; the test asserts equality."""
    accounting = ((ref.W - attack.W) + (attack.profit[focal] - ref.profit[focal])) / attack.sstar
    direct = (_others_utility(ref, focal) - _others_utility(attack, focal)) / attack.sstar
    return float(accounting), float(direct)
```

```python
# scripts/run.py
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from touchstone.config import MarketConfig
from touchstone.market import run_episode
from touchstone.mechanisms.posted import PostedPrices
from touchstone.mechanisms.posted_audit import PostedRandomAudit
from touchstone.mechanisms.second_score import SecondScore
from touchstone.metrics import summarize
from touchstone.policies.honest import HonestMax


def make_rule(name: str):
    if name == "B1":
        return PostedPrices(0.25, 0.40, 0.55)
    if name == "B2":
        return PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    if name == "B3":
        return SecondScore(tol=0.12, L=10)
    raise SystemExit(f"unknown rule {name}")


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
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        w.writeheader()
        w.writerow({k: (f"{v:.12g}" if isinstance(v, float) else v) for k, v in row.items()})


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_metrics.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add touchstone/metrics.py scripts/run.py tests/test_metrics.py
git commit -m "feat: metrics, gain and harm against a reference run, run script"
```

---

### Task 10: Pilot gate benchmark and hot-path vectorization

**Files:**
- Create: `scripts/bench.py`
- Modify: `touchstone/market.py` (hot paths), `touchstone/mechanisms/posted.py` (allocation loop)
- Test: `tests/test_bench.py`

**Interfaces:**
- Produces: `scripts/bench.py` printing median wall time per `T = 200` B2 episode over 20 runs after 3 warm-ups; exit code 1 if the median exceeds 45 ms. `bench_episode_ms(n_runs: int) -> float` importable from `scripts/bench.py` for the test.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bench.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_pilot_gate_loose_bound_in_ci():
    # CI machines vary; the hard 45 ms gate is checked by running scripts/bench.py by hand.
    from bench import bench_episode_ms
    ms = bench_episode_ms(n_runs=5)
    print(f"median episode time: {ms:.1f} ms")
    assert ms < 400.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bench.py -v -s`
Expected: FAIL with `ModuleNotFoundError: No module named 'bench'`

- [ ] **Step 3: Write the benchmark, then vectorize until the hard gate passes**

```python
# scripts/bench.py
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from touchstone.config import MarketConfig
from touchstone.market import run_episode
from touchstone.mechanisms.posted_audit import PostedRandomAudit
from touchstone.policies.honest import HonestMax
from touchstone.rng import make_draws

GATE_MS = 45.0


def bench_episode_ms(n_runs: int = 20, warmups: int = 3) -> float:
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=200, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=3.0)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    pols = [HonestMax() for _ in range(cfg.N)]
    draws = make_draws(cfg, seed=0)      # draws are precomputed per seed and shared across cells
    for _ in range(warmups):
        run_episode(cfg, rule, pols, 0, draws=draws)
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        run_episode(cfg, rule, pols, 0, draws=draws)
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times)


if __name__ == "__main__":
    ms = bench_episode_ms()
    print(f"median T=200 B2 episode: {ms:.1f} ms (gate {GATE_MS} ms)")
    sys.exit(0 if ms <= GATE_MS else 1)
```

Then run `uv run python scripts/bench.py`. If the median is above 45 ms, apply these three changes in order and re-measure after each; stop when the gate passes.

Change A, `touchstone/mechanisms/posted.py`: replace the per-job Python eligibility scan with one NumPy pass per round. Precompute arrays once per `allocate` call: `claim_arr[N]` (NaN for abstainers or inactive), `tier_arr[N]`, `price_of_provider[N]`. For each job in value order, eligibility is `(cap > 0) & active & (v * claim_arr >= price_of_provider)`; pick the highest tier among eligible with `tier_arr[mask].max()`, then choose uniformly among `np.flatnonzero(mask & (tier_arr == best))` with `op_rng.integers`.

```python
    def allocate(self, values_t, offers, state, op_rng):
        N = state.N
        cap = state.capacity_left
        claim_arr = np.full(N, np.nan)
        for i, off in offers.items():
            if state.is_active(i):
                claim_arr[i] = off.claim
        tier_arr = np.array([self.tier_of(c) if not np.isnan(c) else -1 for c in claim_arr])
        price_arr = np.where(tier_arr >= 0, np.array(self.prices)[np.clip(tier_arr, 0, 2)], np.inf)
        order = np.argsort(-values_t, kind="stable")
        assignment = {}
        for j in order:
            v = values_t[j]
            mask = (cap > 0) & (tier_arr >= 0) & (v * np.nan_to_num(claim_arr) >= price_arr)
            if not mask.any():
                continue
            best = tier_arr[mask].max()
            cands = np.flatnonzero(mask & (tier_arr == best))
            chosen = int(cands[op_rng.integers(len(cands))])
            assignment[int(j)] = chosen
            cap[chosen] -= 1
        return assignment
```

Change B, `touchstone/market.py`: build `ProviderView` objects without allocating a new `np.random.default_rng` for honest policies. Keep the keyed seed in the view and construct the generator lazily: change `ProviderView.rng` to a property backed by `policy_seed: int`.

```python
@dataclass(frozen=True)
class ProviderView:
    i: int
    params: ProviderParams
    t: int
    posted_prices: tuple[float, ...] | None
    history: ProviderHistory
    policy_seed: int

    @property
    def rng(self) -> np.random.Generator:
        return np.random.default_rng(self.policy_seed)
```

Update the `ProviderView(...)` construction in `market.py` to pass `policy_seed=int(d.policy_seed[t, i])`, and `tests/test_policies.py::view` to pass `policy_seed=0`.

Change C, `touchstone/market.py`: replace the per-job `ledger.charge_cost` loop and the per-job value accumulation with array operations per round:

```python
        if assignment:
            jobs = np.fromiter(assignment.keys(), dtype=np.int64, count=len(assignment))
            provs = np.fromiter(assignment.values(), dtype=np.int64, count=len(assignment))
            counts = np.bincount(provs, minlength=cfg.N)
            slots = np.zeros(len(provs), dtype=np.int64)
            seen = np.zeros(cfg.N, dtype=np.int64)
            for n, i in enumerate(provs):
                slots[n] = seen[i]; seen[i] += 1
            y = effort[provs] + d.noise[t, provs, slots]
            value_total += float((values_t[jobs] * y).sum())
            ledger.cost += counts * (a_arr + b_arr * effort)
            served[t] = counts
            delivered = dict(zip(jobs.tolist(), y.tolist()))
        else:
            delivered = {}
```

with `a_arr = np.array([p.a for p in cfg.providers])` and `b_arr = np.array([p.b for p in cfg.providers])` computed once before the loop.

- [ ] **Step 4: Run the full test suite and the benchmark**

Run: `uv run pytest -v && uv run python scripts/bench.py`
Expected: all tests PASS; benchmark prints a median at or below 45 ms and exits 0. Record the measured number in the commit message.

- [ ] **Step 5: Commit**

```bash
git add scripts/bench.py tests/test_bench.py touchstone/market.py touchstone/mechanisms/posted.py touchstone/policies/base.py tests/test_policies.py
git commit -m "perf: pilot gate benchmark; vectorized allocation and delivery (median NN ms)"
```

---

### Task 11: Spec amendments and README status

**Files:**
- Modify: `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (section 7, common random numbers; section 14, new entry)
- Modify: `README.md` (Status line)

**Interfaces:** none.

- [ ] **Step 1: Record the RNG keying decision in the spec**

In section 7, replace the sentence beginning "Job values and delivery noise are drawn from `numpy.random.SeedSequence` children keyed by (seed, round, job)" with:

```
Job values, delivery noise, operator randomness, and policy randomness for
round t are a pure function of (seed, t), drawn in a fixed order and laid out
in fixed positions (job index; provider index and slot index), from a
`numpy.random.SeedSequence([seed, t])` child. No action can change any draw of
any round, which `tests/test_rng.py` and `tests/test_market.py` check. One
child per round rather than per job keeps an episode under the pilot gate.
```

Append to section 14:

```
Implementation (plan 1, core engine): draws keyed per (seed, round) with
fixed intra-round layout instead of per (seed, round, job); same
action-independence property, tested; chosen for the 45 ms gate.
```

- [ ] **Step 2: Update the README status**

Replace the README's `## Status` body with:

```
Week 1. Core engine implemented: market, ledger, first-best, B1 to B3,
honest-max and fixed-cheat policies with the truthful twin, metrics, run
script, and the pilot benchmark. Plan 2 (search, families, manifest,
calibration, tuning, coverage study, claim script, model actors) next.
```

- [ ] **Step 3: Run the whole suite once more**

Run: `uv run pytest -q`
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md README.md
git commit -m "docs: record RNG keying in the spec; README status after plan 1"
```

---

## Self-review

**Spec coverage for this plan's scope.** Section 3 (jobs, providers, delivery, claim semantics, round sequence, observations, budget, validity): Tasks 2, 5, 6. Section 4 interface and 4.0 class: Task 4 (types, validation), Task 5 (ledger applies), Task 7 (refund and ban), hold-backs accepted and settled at the end (Task 5) with forfeit schedules deferred to plan 3 as stated in the scope split. Section 4.1 B1, B2, B3: Tasks 6, 7, 8, including the spread schedule's three caps and the worked example. Section 5.1 views and actions, 5.2 honest-max and twin, 5.3 D1 with the clip knob: Task 6. Section 7 S*, ledger, W, gross and net efficiency, audit spend, gain, harm with the identity test, CRN: Tasks 3, 5, 9, with the keying recorded in Task 11. Section 12 tests named in scope: honest-max equals its twin; all-honest mean gross efficiency; one-provider closed form; byte-identical CSV; budget never exceeded, per-round cap, fractional last round; spread schedule expectation and repeated-seed criterion; B1 fixture positive gain; deviation does not change later draws; cash conservation and harm identity; interface rejects an effort field; honest failure rate; S* > 0 on valid configs; twin never exceeds effort; shared harness run per mechanism with the B3 worked example. Not in this plan, by the scope split: search checks, locked-config hash, sealed-bundle hash, `describe()` tests, LLM replay, coverage study, exclusion-duration ablation tests.

**Placeholder scan.** No TBD, TODO, or "handle edge cases". Every step carries code or an exact command.

**Type consistency.** `Offer(claim, bid)`; `Consequences(refunds, bans, holdbacks)`; `Mechanism.allocate(values_t, offers, state, op_rng)` carries `op_rng` as its fourth parameter in Task 4's abstract signature and in every implementation and call in Tasks 6 to 8. `OperatorState.capacity_left` and `escrow_of` are set by `run_episode` before `allocate` and `audit` respectively, and tests that call `allocate` directly set `capacity_left` themselves. `ProviderView.rng` becomes a property in Task 10 and the Task 6 tests are updated there. `EpisodeResult.draws_id` is the Python id of the shared `Draws` object, used only by the CRN test. `gain` and `harm` take `(attack, ref, focal)` everywhere.

**Review Focus.** Item 1 (all banned) and item 2 (budget below one audit) and item 5 (negative delivery): Task 7 tests. Item 3 (capacity above jobs): Task 3 and Task 6 tests. Item 4 (tied values): Task 6 test.
