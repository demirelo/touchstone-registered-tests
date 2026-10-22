# Revision program, build phase: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and test, on development seeds only, every piece of code that the accepted revision-program design needs before paid runs: the factorial, credibility, and repaired rules; the new attack families and objectives; the reference freeze; the market generator, seed streams, and block reader; the inference and calibration code; the v2 runner and manifest; tuning, coverage, and benchmark entry points.

**Architecture:** New rules live in `sim/mechanisms/` and share one pacing module and B3's allocation. New families live in `sim/policies/` and take the rule's public T and L at construction. A new runner, `scripts/revision_v2.py`, reuses the frozen search and reference primitives (`sim/search.py`, `sim/reference.py`, `sim/cell.py`) and writes one validated record per stage; it never imports `scripts/explore_attackers.py`, whose development-salt and locked-seed checks do not apply to fresh markets. Statistics live in `sim/intervals.py` (extended) and `sim/calibration_v2.py`.

**Tech Stack:** Python 3 with uv, numpy, scipy 1.18.1 (pinned in `uv.lock`), cma, pytest.

**Spec:** `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 6, accepted; cited as "design"). The simulator specification `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` ("spec") still binds the admissible class (spec 4.0).

## Global Constraints

- Development data only: seeds dev-train 1000-1004, dev-val 2000-2019, calibration 4000-4019, coverage pools in [40,000,000, 60,000,000); the development salt; development root "dev-20261022". No fresh-root data exists during this plan.
- No paid API calls in tests. No network in tests (block-reader tests use recorded fixtures).
- Frozen files stay byte-identical to branch base `2a288f5`: `sim/mechanisms/proposed.py`, `second_score.py`, `audit_random.py`, `sim/policies/exploratory.py`, `sim/policies/adaptive.py`, `sim/policies/identity.py`, `sim/search.py`, `sim/reference.py`, `sim/market.py`, `scripts/explore_attackers.py`, `experiments/locked.yaml`, `experiments/proposed.yaml`. A test compares each file's bytes with `git show 2a288f5:<path>`.
- Every rule reads only spec 4.0 inputs; decisions are invariant to relabelling identity tokens.
- The fixed pair is tol = 0.16, L = 10 (design 3.1). The common grid is tol in {0.08, 0.12, 0.14, 0.16} x L in {3, 10, 20, 50} (design 4.2).
- Code style matches the surrounding code: dense module docstrings that cite the design section, short helper names, no chat formatting in comments.
- Commits are unsigned (`git -c commit.gpgsign=false`) and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Test command for the whole suite: `uv run pytest -q`; slow matrices: `uv run pytest -q --runslow -m slow` (the repository's `--runslow` flag, `tests/conftest.py`).
- Pod entry: `results/pods/explore_pod.sh` appends `--workers N --out DIR` to `SCRIPT ARGS` and unsets `TOUCHSTONE_IDENTITY_SALT` in the remote shell; every v2 CLI accepts `--workers` and installs any non-development salt inside its own process.

## Review Focus

1. **Exit-round actions.** The harness asks for the action before it creates the replacement and applies the exit before the offer. X7-SC, X5-AG/v2, and X6-SE/v2 must give the replacement's phase in the exit round (design 5.2 step 5). Pinned by Task 4 `test_x7_exit_round_phase_is_replacement` and Task 5 `test_v2_families_match_v1_at_headline_constants`.
2. **Budget exhaustion and empty rounds.** Every new rule must audit nothing when `audits_left == 0` or when no job is served, and must never audit more than the served jobs. Pinned by Task 1 and Task 2 property tests over all cells.
3. **Evaluation before freeze.** Any evaluation-seed episode of a market before that market's final freeze must refuse (design 6.4). Pinned by Task 11 `test_evaluate_refuses_before_final_freeze` and `test_accept_refuses_supplied_incomplete_freeze`.
4. **Seed-range collisions.** A fresh or coverage seed must never coincide with a development, calibration, amendment, or first-final-evaluation seed. Pinned by Task 6 `test_seed_ranges_disjoint`.
5. **Resume after a crash.** A stage whose record exists and validates must not rerun; a record with a different provenance must refuse. Pinned by Task 11 `test_resume_skips_valid_and_refuses_foreign`.

---

### Task 1: Pacing module, factorial rules, and R4

**Files:**
- Create: `sim/mechanisms/pacing.py`, `sim/mechanisms/factorial.py`, `tests/oracles/__init__.py`, `tests/oracles/predecessor_46694cb.py` (verbatim `git show 46694cb:sim/mechanisms/proposed.py`, one header comment naming the source commit), `tests/test_factorial.py`, `tests/test_frozen_files.py`
- Test helpers: `tests/_v2_profiles.py` (policy profiles shared by Tasks 1, 2, 4, 5)

**Interfaces:**
- Produces: `pacing.spread_count(view, T, cap_per_round, n_served) -> int` (wraps `audit_random.spread_audit_count`); `pacing.ReservePacing(reserve: str, L: int)` with `reserve in ("full", "half")`, `bind(cfg)` (reads T, J, budget, alpha), `count(view, n_served) -> int`, which reads and writes `view.memory["quota_carry"]` exactly as `Proposed.audit` does, with reserve min(J L, A_tot) for "full" and min(J L, A_tot // 2) for "half", terminal rounds t >= T - L.
- Produces: `factorial.FactorialRule(P: int, G: int, S: int, tol: float, L: int, reserve: str = "full")`, a `Mechanism` named `F{P}{G}{S}` (R4: `name = "R4"`, P = G = S = 1, reserve "half"); `factorial.make_factorial(name: str, tol: float, L: int) -> FactorialRule` for `F000` to `F111` and `R4`.
- Memory as `Proposed`: `first_round` (set at the identity's first active offer in `allocate`), `audits`, `served`, `quota_carry`; allocation and payment reimplement B3 (`SecondScore.allocate`, `price` semantics); enforcement is refund and a ban of L.
- Selection of k jobs, in two independent phases:
  - Priority (P = 1 only): served jobs of identities with 0 <= t - first_round < L, ordered by (-first_round, audit_key, job), up to k; counted in `audits` first.
  - Residual on r = k - q: if G = 1, ceil(r/2) picks by (-first_round, audit_key, job) one at a time, then floor(r/2) uniform by (audit_key, job); if G = 0, all r uniform.
  - Uniform tie rule: when P = G = 0, uniform order is B3's (`numpy.argsort(audit_key[jobs], kind="stable")` over jobs in assignment order); otherwise R3's (audit_key, job). Ties occur only in the `tied_keys` profile.
- Produces for tests: `tests/_v2_profiles.py::PROFILES: dict[str, callable]` with keys `honest`, `abstain_mix`, `replacement` (D2+H3 x = 1 knobs that fail often), `ban_return` (D2 knobs that fail, no exit), `tied_keys` (a draws override with equal audit keys), `empty_rounds` (all abstain in some rounds); `run_full(cfg, rule, profile, seed) -> EpisodeResult`; `fingerprint(res) -> dict` (round records, plus profit, cost, entry, audit_cost, W, buyer_surplus, identity_profit, and the ledger's terminal settlement).

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("tol,L", COMMON_GRID)            # the 16 pairs
@pytest.mark.parametrize("profile", PROFILE_NAMES)
@pytest.mark.parametrize("seed", SEEDS)                   # [2000] by default; 2000-2004 under --runslow -m slow
def test_f000_equals_b3(tol, L, profile, seed):
    assert fingerprint(run_full(CFG, make_factorial("F000", tol, L), profile, seed)) == \
           fingerprint(run_full(CFG, SecondScore(tol, L), profile, seed))

# same parametrisation:
def test_f111_equals_r3(...):            # make_factorial("F111", tol, L) vs proposed.Proposed("A", "T1", tol, L)
def test_f011_equals_predecessor(...):   # vs tests.oracles.predecessor_46694cb.Proposed("A", "T1", tol, L)
def test_p1_g0_residual_is_uniform():    # hand-built round: after the priority phase, the residual follows (audit_key, job) only
def test_r4_reserve_is_half_allowance(): # at rho = 1 (A_tot == J L): R4's early-quota sum == A_tot - A_tot // 2; R3's == 0
def test_positive_quota_audits_every_cell():   # every cell, every round with k > 0 and service > 0: len(audits) == min(k, served, audits_left)
def test_relabelling_invariance():       # permute identity tokens of a recorded profile; every F cell and R4 picks the same jobs
def test_no_audit_when_budget_or_service_empty():   # every cell: audits_left == 0 or no service -> []; never more than served
def test_frozen_files_unchanged():       # bytes of each frozen file == git show 2a288f5:<path>
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `uv run pytest tests/test_factorial.py tests/test_frozen_files.py -q`
Expected: FAIL with `ModuleNotFoundError: sim.mechanisms.factorial`; `test_frozen_files_unchanged` passes.

- [ ] **Step 3: Implement `sim/mechanisms/pacing.py` and `sim/mechanisms/factorial.py`** as the interfaces state; S = 0 uses `spread_count` with B3's cap from `bind`, S = 1 uses `ReservePacing`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `uv run pytest tests/test_factorial.py tests/test_frozen_files.py -q && uv run pytest tests/test_factorial.py -q --runslow -m slow`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sim/mechanisms/pacing.py sim/mechanisms/factorial.py tests/oracles tests/_v2_profiles.py tests/test_factorial.py tests/test_frozen_files.py
git -c commit.gpgsign=false commit -m "factorial rules F000-F111 and R4 on a shared pacing module; oracles: B3, R3, the 46694cb predecessor"
```

### Task 2: Credibility rules

**Files:**
- Create: `sim/mechanisms/credibility.py`, `tests/test_credibility.py`

**Interfaces:**
- Consumes: `pacing.spread_count`, `pacing.ReservePacing(reserve, L)` (Task 1); B3 allocation.
- Produces: `credibility.Credibility(variant: str, K: int, tol: float, L: int, pacing: str, M: int | None = None)` with `variant in ("thr", "mem", "taper")`, `pacing in ("S0", "S1", "S2")` (S1 = reserve "full", S2 = reserve "half"); `name` = `C-{variant}` plus `/S0` or `/S2` when not S1; `credibility.make_credibility(params: dict) -> Credibility`; `credibility.SELECTION_GRID` = the 12 configurations of design 3.3 in the order thr K 2, 6, 12, 24; mem (K, M) (2, 20), (2, 50), (6, 20), (6, 50); taper K 2, 6, 12, 24.
- Memory: `view.memory["passes"]: dict[int, list[tuple[int, int]]]` (round, passes) per identity, cleared on a failure; `view.memory["last_fail"]: dict[int, int]`.

- [ ] **Step 1: Write the failing tests**

```python
def test_batch_failure_resets_even_with_passes():   # one pass and one failure of identity i in round t -> p_i(t + 1) == 0
def test_counts_from_start_of_round():              # an audit chosen in round t does not raise p_i within round t
def test_ban_return_starts_at_zero():               # after the ban, the identity's first selection sees p_i == 0
def test_thr_priority_then_residual_order():        # hand-built round: unproven jobs first by (p, key, job); residual ceil(r/2) by (p + picks, key, job)
def test_mem_window_boundary():                     # passes at round max(f_i + 1, t - M) included; t - M - 1 and rounds <= f_i excluded
def test_taper_weights_and_race():                  # w = K / (p + K); chosen jobs == k smallest -log(key) / w, ties by job index
def test_taper_new_identity_weight_one():
def test_pacing_variants_match_factorial_counts():  # per round, the count k of C/S0, C, C/S2 equals F000's, F111's, R4's on the same records
def test_selection_grid_order_and_size():           # 12 entries, exact order above
def test_relabelling_invariance_credibility():
def test_no_audit_when_budget_or_service_empty_credibility():
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `uv run pytest tests/test_credibility.py -q`
Expected: FAIL with `ModuleNotFoundError: sim.mechanisms.credibility`.

- [ ] **Step 3: Implement `sim/mechanisms/credibility.py`** following design 3.3 exactly; the pass update runs in `enforce`, from the round's audit records, before consequences are returned.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `uv run pytest tests/test_credibility.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sim/mechanisms/credibility.py tests/test_credibility.py
git -c commit.gpgsign=false commit -m "credibility comparator: threshold, finite-memory, and taper variants with S0, S1, S2 pacing"
```

### Task 3: Rule registry v2

**Files:**
- Create: `sim/rules_v2.py`, `tests/test_rules_v2.py`

**Interfaces:**
- Consumes: Tasks 1 and 2; `sim/tuning.rule_from_params` for B2.
- Produces: `rules_v2.make_rule(name: str, tol: float = 0.16, L: int = 10, cred: dict | None = None, b2_params: dict | None = None) -> Mechanism` for `F000`..`F111`, `R4`, `C*`, `C*/S0`, `C*/S2` (from `cred` = `{"variant", "K", "M"}`), `B3-t`, `R3-t`, `R4-t`, `C*-t` (tuned `tol`, `L`), and `B2` (registered parameters); `rules_v2.MATCHED` (the 12 matched names) and `rules_v2.CORE` (`F000`, `F111`, `C*`, `R4`).
- Public-constant contract: `rules_v2.public_constants(rule: Mechanism, cfg: MarketConfig) -> dict` returns `{"T": cfg.T, "L": rule.describe()["parameters"]["ban_length"]}`. T is part of the locked market configuration, which spec 4.0 makes public; L is read only from the rule's describe record (frozen rules already carry `ban_length` there). Families are constructed per cell from these constants before any episode; no rule needs to be bound first.

- [ ] **Step 1: Write the failing tests**

```python
def test_make_rule_names_and_types():          # each name builds; F111 at the fixed pair has name "F111", tol 0.16, L 10
def test_public_constants_nondefault():        # a market with T = 100 and make_rule("C*", L=20, cred=...) -> {"T": 100, "L": 20}
def test_public_constants_frozen_rules():      # SecondScore(0.16, 10) and Proposed("A", "T1", 0.16, 10) -> L 10 from describe
def test_unknown_name_refuses():
def test_matched_and_core_lists():
def test_admissibility_inputs():               # each rule runs with entity ids absent from its view (identity tokens only)
```

- [ ] **Step 2: Run** `uv run pytest tests/test_rules_v2.py -q`; expected FAIL with `ModuleNotFoundError`.
- [ ] **Step 3: Implement `sim/rules_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_rules_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add sim/rules_v2.py tests/test_rules_v2.py && git -c commit.gpgsign=false commit -m "rule registry v2: matched, tuned, and reference rules with public constants"`

### Task 4: X7-SC family

**Files:**
- Create: `sim/policies/x7.py`, `tests/test_x7.py`

**Interfaces:**
- Consumes: `AdaptiveCheat`'s recurrence (reimplemented, so its state persists across identities as D2+H3's does); `families.Family`; `exploratory.IdentityState(T, W=L)` by composition.
- Produces: `x7.X7Policy(u0, m0, s, d, r, w, k_F, k_T, a_F, n_P, h_R, lam, clip, T: int, L: int)` with diagnostics `resets_failure`, `resets_voluntary`, `last_phase`; `x7.x7_family(T: int, L: int) -> Family` named `X7-SC`, knobs in design 5.2 order with the knob named `lambda`; its factory maps `lambda` to `lam` and binds T and L; `x7.embed_h3(knobs: dict, T: int) -> dict`; `x7.x7_corners(family) -> list[dict]` (design 5.2 Sobol construction, 514 corners); `x7.corner_vectors(family) -> list[dict]` (corners plus truthful projections, de-duplicated by exact key, 769 with scipy 1.18.1). The runner never calls `family.corners()` for X7-SC (it would enumerate 8,192 corners); Task 11 tests that.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("rule_name", ["F000", "F111", "C*", "R4", "C*/S2"])
@pytest.mark.parametrize("tol,L", GRID_FOR_SEEDS)          # fixed pair by default; the 16 common pairs under --runslow -m slow
@pytest.mark.parametrize("seed", SEEDS)                   # [2000] by default; 2000-2004 under --runslow -m slow
def test_embedding_equals_d2h3(x, rule_name, tol, L, seed):
    k = {**D2_KNOBS_FAILING, "x": x}
    rule = make_rule(rule_name, tol, L, cred=CRED)
    a = run_full(CFG, rule, focal(h3_family(D2).make(k)), seed)
    b = run_full(CFG, make_rule(rule_name, tol, L, cred=CRED), focal(x7_family(200, L).make(embed_h3(k, 200))), seed)
    assert fingerprint(a) == fingerprint(b)
    assert (count_exits(a) > 0) == (x == 1)

def test_transition_order():               # hand-fed views: markup updated once; failure trigger before voluntary; exit clears identity counters
def test_x7_exit_round_phase_is_replacement():   # forced failure, h_R = 0, k_F = 0: in the exit round last_phase == "fresh", effort == q_max,
                                                 # claim == min(1, max(0, q_max - s)) and bid == (1 + w)(a + b q_max)
def test_voluntary_reset_window_and_zero_service():   # window [max(c, t - L), t); served == 0 -> no reset; lambda = 1 never resets
def test_terminal_phase_uses_injected_L():   # T = 200, L = 20: rounds 180..199 terminal
def test_lambda_knob_maps_to_lam():
def test_corners_construction():             # 512 distinct Sobol corners, neither endpoint, 514 after appending; 769 vectors with projections
def test_x7_contains_its_twin():             # project(knobs) gives claim <= effort every round
def test_x7_observations_only_view():        # X7Policy.act reads only ProviderView fields and its constructor constants
```

- [ ] **Step 2: Run** `uv run pytest tests/test_x7.py -q`; expected FAIL with `ModuleNotFoundError`.
- [ ] **Step 3: Implement `sim/policies/x7.py`** following design 5.2 steps 1 to 6.
- [ ] **Step 4: Run** `uv run pytest tests/test_x7.py -q && uv run pytest tests/test_x7.py -q --runslow -m slow`; expected PASS.
- [ ] **Step 5: Commit** `git add sim/policies/x7.py tests/test_x7.py && git -c commit.gpgsign=false commit -m "X7-SC state-conditioned family with exact D2+H3 embedding and Sobol corner controls"`

### Task 5: X5-AG/v2 and X6-SE/v2 with injected constants

**Files:**
- Create: `sim/policies/v2.py`, `tests/test_policies_v2.py`

**Interfaces:**
- Consumes: `exploratory.X5Policy`, `X6Policy`, `IdentityState`, `scheduled_resets`, `coalition_members` (imported, not modified).
- Produces: `v2.x5v2_family(T: int, L: int) -> Family` (`X5-AG/v2`, `n_age` in [0, 60]); `v2.x6v2_family(T: int, L: int) -> Family` (`X6-SE/v2`, X6-SE's knobs); `v2.x6v2_members(cfg, focal: int, c: int) -> tuple[int, ...]` (delegates to `coalition_members`); member policies take `member`, `c`, `staggered`.
- Approach: subclasses that replace the policy's `IdentityState()` with `IdentityState(T, L)` and compute schedules with `scheduled_resets(P, c, T, staggered)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_v2_families_match_v1_at_headline_constants():   # T = 200, L = 10, profiles with forced failures (X5, x = 1) and scheduled exits
                                                         # (X6, y = 1): identical fingerprints to X5-AG and X6-SE, and count_exits > 0
def test_x5v2_exit_round_action_nondefault():            # T = 100, L = 20, forced failure: the exit-round action is the replacement's (honest while age < n_age)
def test_x6v2_schedule_uses_injected_T():                # T = 100: exits at k P' for k = 1..floor(99 / P'), observed in the run
def test_x5v2_age_bound_60():
def test_members_order():                                # equals coalition_members on the headline and on dev0
```

- [ ] **Step 2: Run** `uv run pytest tests/test_policies_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement `sim/policies/v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_policies_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add sim/policies/v2.py tests/test_policies_v2.py && git -c commit.gpgsign=false commit -m "X5-AG/v2 and X6-SE/v2 with the rule's public T and L"`

### Task 6: Market generator and streams

**Files:**
- Create: `sim/instances.py`, `tests/test_instances.py`

**Interfaces:**
- Produces: `instances.digest(root: str, domain: str, n: int) -> bytes`; `instances.stream(root: str, i: int) -> numpy.random.Generator`; `instances.draw_instance(rng, limit: int = 10_000) -> tuple[MarketConfig, int]` (config before calibration, rejection count; raises `InstanceLimit` at the limit). Draw order inside one attempt: q_max (10 uniforms), b_lo, b_hi, the 10 b noises, a (10), k (10 integers), v_max. `instances.markets(root: str, count: int) -> list[dict]` with entries `{"label", "stream_index", "cfg", "rejections"}`: label `fresh<i>` uses stream i; if stream i hits the limit, label `fresh<i>` takes the next unused stream index >= count (6, 7, ...), and the other labels keep their own streams (design 7.2); `instances.dev_markets() -> list[dict]` (`dev0`, `dev1` from root "dev-20261022"); `instances.calibrated(cfg) -> MarketConfig` (frozen `calibrate` on seeds 4000-4019, beta 0.05, rho 0.2 via `cell_config`); `instances.eval_seeds(root: str, label: str, n: int = 200) -> list[int]`; `instances.identity_salt_hex(root: str) -> str`; `instances.coverage_pool(label: str, n: int = 20_000) -> list[int]` (range [40,000,000, 60,000,000), domain "coverage/" + label, root "dev-20261022").

- [ ] **Step 1: Write the failing tests**

```python
def test_digest_encoding():               # digest("r", "d", 3) == sha256(b"r|touchstone-v2|d|3").digest()
def test_stream_is_index_independent():   # stream(root, 1) does not depend on whether stream 0 was drawn
def test_draw_fixed_parameters_and_ranges():   # N 10, J 50, T 200, sigma 0.05, e 0, v_min 0.6; q_max sorted in [0.55, 1]; k in 4..8; v_max in [1.2, 1.6]
def test_b_is_decreasing_in_rank_up_to_noise():
def test_draw_passes_validate():
def test_limit_replacement_keeps_label_order():   # stream 0 forced to fail: fresh0 -> stream 6, fresh1..fresh5 -> streams 1..5 (assert stream_index)
def test_eval_seeds_range_unique_and_count():     # 200 unique values in [30e6, 40e6); int.from_bytes(..., "big")
def test_seed_ranges_disjoint():                  # eval range, coverage range vs dev-train, dev-val, calibration, amendment-1 block, final-eval range
def test_draw_matches_independent_reimplementation():   # the test re-draws dev0's first attempt from a fresh copy of the stream in the stated
                                                        # draw order with its own arithmetic and compares every field
```

- [ ] **Step 2: Run** `uv run pytest tests/test_instances.py -q`; expected FAIL.
- [ ] **Step 3: Implement `sim/instances.py`** per design 7.1 and 7.2.
- [ ] **Step 4: Run** `uv run pytest tests/test_instances.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add sim/instances.py tests/test_instances.py && git -c commit.gpgsign=false commit -m "market generator, domain-separated streams, evaluation and coverage seeds"`

### Task 7: Block reader

**Files:**
- Create: `scripts/block_draw.py`, `tests/test_block_draw.py`, `tests/fixtures/btc_headers.json` (11 consecutive real mainnet headers in hex with their heights, starting at height 971818, the lowest Bitcoin attestation of `docs/lock-2026-10-17.txt.ots`; recorded once with curl before the test is written; the recording command is in the test's docstring), `tests/fixtures/lock_ots_info.txt` and `tests/fixtures/lock_ots_verify.txt` (the `ots info` and `ots verify` outputs of that proof)

**Interfaces:**
- Produces: `block_draw.header_hash(raw: bytes) -> str` (double SHA-256, reversed hex); `block_draw.target_from_bits(bits: int) -> int`; `block_draw.verify_chain(headers: list[bytes], first_hash: str) -> list[str]` (raises on a first-hash mismatch, a broken link, or insufficient proof of work; returns the hashes in order); `block_draw.attestations(ots_info_output: str) -> list[tuple[int, str]]` (every `BitcoinBlockHeaderAttestation(<height>)` with the following `# Bitcoin block merkle root <hex>` line); `block_draw.verified_height(ots_verify_output: str) -> int` (the height in the successful `Success! Bitcoin block <height> attests` line; refuses output without it); `block_draw.anchor(ots_info_output: str, ots_verify_output: str) -> dict` (`{"height", "merkle_root"}` of the attestation at the verified height, taken from the `ots info` listing; refuses if that height is not listed). The OpenTimestamps client skips failed attestations and reports the first success, so the anchor is the verified attestation, not the lowest listed one; `block_draw.merkle_root(raw: bytes) -> str` (header bytes 36..68, reversed hex); `block_draw.target_height(anchor_height: int, offset: int = 144) -> int`; `block_draw.read_final(anchor: dict, fetch, offset: int = 144, depth: int = 6) -> dict` with `fetch(source, path) -> str` injected for the two sources. `read_final` requires both sources' tip >= H + depth and both sources' hashes at H to agree; it downloads headers A..H + depth from the first source, requires the first header's Merkle root to equal the anchor's Merkle root (the protocol commitment, from the proof itself) and both sources' hashes at A to equal that header's hash, runs `verify_chain` from it, and requires the chain's hash at position H - A to equal the agreed H hash; otherwise it returns `{"status": "wait"}` (disagreement, low tip) or raises (verification failure). CLI `--ots PATH --out PATH` runs `ots verify` (which must succeed) and `ots info` on the proof, then polls hourly and writes the block hash, the headers, and both sources' answers.

- [ ] **Step 1: Write the failing tests**

```python
def test_header_hash_matches_fixture():
def test_verify_chain_accepts_fixture():
def test_verify_chain_rejects_tampered_link_bits_and_first_hash():
def test_anchor_is_verified_attestation_and_merkle_root():   # lock fixtures -> height 971818 and its merkle root; equals merkle_root(fixture header 0)
def test_anchor_skips_failed_lower_attestation():   # synthetic info with a lower attestation and verify output naming the higher: the higher is chosen
def test_anchor_refuses_without_bitcoin_attestation():
def test_read_final_waits_on_disagreement_or_low_tip():
def test_read_final_returns_agreed_hash():          # fixture anchor, offset 4, depth 6: H hash == chain[4] == both sources
def test_read_final_rejects_unrelated_chain():      # sources agree on H but the headers start from another valid chain
def test_read_final_rejects_explorers_agreeing_on_other_anchor():   # both sources agree on a different hash at A, with an internally valid chain
def test_read_final_rejects_truncated_chain():
def test_read_final_rejects_h_position_mismatch():
```

- [ ] **Step 2: Run** `uv run pytest tests/test_block_draw.py -q`; expected FAIL.
- [ ] **Step 3: Implement `scripts/block_draw.py`** (stdlib `hashlib`; `urllib.request` and `subprocess` only in the CLI path).
- [ ] **Step 4: Run** `uv run pytest tests/test_block_draw.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add scripts/block_draw.py tests/test_block_draw.py tests/fixtures/btc_headers.json tests/fixtures/lock_ots_info.txt tests/fixtures/lock_ots_verify.txt && git -c commit.gpgsign=false commit -m "block reader: verified anchor, header chain from A to H + 6, two-source agreement"`

### Task 8: Intervals, tests, calibration primitives, and decision rules

**Files:**
- Modify: `sim/intervals.py` (add functions; existing functions unchanged)
- Create: `sim/decisions_v2.py`, `tests/test_intervals_v2.py`, `tests/test_decisions_v2.py`

**Interfaces:**
- Produces in `sim/intervals.py`: `studentized_tstats(x, resamples: int, seed: int) -> tuple[float, float, ndarray]` (mean, se, t-statistics; existing constancy and zero-se conventions); `studentized_at(x, side: str, tail: float, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float`; `bootstrap_pvalue(x, null: float, side: str, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float` (smallest tail whose bound crosses `null`, at resolution 1 / (resamples + 1); constant data give 0 or 1 by the side of the null; an unattainable crossing gives 1); `two_sided_pvalue(x, null, ...) -> float` (2 min of the one-sided p-values, capped at 1); `calibrated(p: float, kappa: float) -> float`; `holm(pvalues: list[float], alpha: float = 0.05) -> list[bool]`; `stratified_tstats(strata: list[ndarray], resamples: int, seed: int)` and `stratified_at(strata, side, tail, ...)`, `stratified_pvalue(strata, null, side, ...)` (equal-weight mean; stratum k resampled with indices from `numpy.random.default_rng(numpy.random.SeedSequence(seed).spawn(K)[k])`; se^2 = sum_k s_k^2 / n_k / K^2); `gmin_bounds(member_rows: list[ndarray], tail: float, ...) -> tuple[float, float]`; `clopper_pearson_upper(x: int, n: int, confidence: float) -> float`; `V2_RESAMPLE_SEED = 20261022`.
- Produces in `sim/decisions_v2.py`: `q1_category(strata_diffs: list[ndarray], kappa: float | None, holm_reject: bool) -> str` (`"R lower"`, `"C lower"`, `"equivalent"`, `"inconclusive"`, or `"no confirmatory decision"` when `kappa is None`; precedence: ordered, then equivalent, then inconclusive); `q1_family(tests: dict, kappa) -> dict` (the 4 pooled tests: calibrated two-sided p-values, Holm, categories); `q2_contrasts(cell_means: dict[str, float]) -> dict` (7 effect-coded contrasts and 4 conditional effects, design 9.3); `q4_markets(pa: list[float], pb: list[float], kappa: float | None) -> dict` (calibrated component p-values, market p = max, Holm over the 6, k passing; `None` kappa suppresses decisions).

- [ ] **Step 1: Write the failing tests**

```python
def test_studentized_at_matches_existing_at_registered_level():   # studentized_at(x, "lower", 0.0125) == studentized_bootstrap(x, "lower", 0.9875, ...).value
def test_pvalue_inverts_bound():          # non-degenerate data: bound at tail p_hat is within one resample step of the null
def test_pvalue_constant_and_unattainable():
def test_two_sided_pvalue():
def test_holm_known_example():            # p = [0.001, 0.04] -> [True, True]; Bonferroni at 0.025 rejects only the first
def test_calibrated_monotone():
def test_stratified_se_formula_and_independent_streams():   # se matches the formula; resamples equal an independent reference that draws
                                          # stratum k's indices from numpy.random.SeedSequence(seed).spawn(K)[k]; a shared-index version differs
def test_gmin_bounds_are_member_minima():
def test_clopper_pearson_known_values():  # x = 88, n = 20000, confidence 1 - 0.01/32 -> about 0.006238; x = 89 exceeds 0.00625
# tests/test_decisions_v2.py
def test_q1_precedence():                 # ordered beats equivalent when both could hold; interval inside the margin without rejection -> equivalent
def test_q1_suppressed_without_kappa():
def test_q2_contrast_coefficients():      # cell means equal to the P bit -> P main effect 1 and both conditional P effects (S = 0, S = 1) 1;
                                          # every other contrast and conditional effect 0; PGS sign on a parity pattern
def test_q4_component_max_then_holm():    # market p = max(calibrated pa, pb); Holm over six; k counted
def test_q4_suppressed_without_kappa():
```

- [ ] **Step 2: Run** `uv run pytest tests/test_intervals_v2.py tests/test_decisions_v2.py -q`; expected FAIL with `ImportError`.
- [ ] **Step 3: Implement the functions in `sim/intervals.py` and `sim/decisions_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_intervals_v2.py tests/test_decisions_v2.py tests/test_intervals.py -q`; expected PASS (existing interval tests unchanged).
- [ ] **Step 5: Commit** `git add sim/intervals.py sim/decisions_v2.py tests/test_intervals_v2.py tests/test_decisions_v2.py && git -c commit.gpgsign=false commit -m "intervals and decisions v2: arbitrary tails, bootstrap p-values, Holm, calibrated p, stratified bounds, Clopper-Pearson, Q1, Q2, Q4 rules"`

### Task 9: Welfare and coalition objectives

**Files:**
- Create: `sim/objectives_v2.py`, `tests/test_objectives_v2.py`

**Interfaces:**
- Consumes: `sim.search.Objective`, `ArchiveEntry`; `sim.cell.run_profile`; `v2.x6v2_family`, `v2.x6v2_members`; `reference.Candidate`.
- Produces: `WelfareObjective(cell, family, cache, ref_normalized: ndarray | None)` maximising `-mean(gross efficiency)`; with `ref_normalized` (W1) it records per-point constraint means `mean((pi - pi_ref) / (S*/N))`; `select_w1(objective) -> dict | None` (feasibility-first on training means; `None` means "no feasible candidate found"); `CoalitionObjective(cfg, rule_factory, members, family, seeds, cache, kind: str, joint_ref: ndarray | None)` with `kind in ("total", "min", "joint_twin")`, where `total` = sum_j mean g_j, `min` = min_j mean g_j, and `joint_twin` = mean of sum_j normalised profit with clip forced; `joint_reference(cell_args, twin_knobs) -> dict` (design 6.3 candidates and tie order, returns per-member reference profits).

- [ ] **Step 1: Write the failing tests**

```python
def test_w0_prefers_lower_efficiency():      # a known sabotage point scores above honest-max
def test_w1_feasibility_first():             # synthetic archive: the lowest-efficiency point is infeasible; selection returns the best feasible
def test_w1_none_when_no_feasible():
def test_coalition_total_vs_min():           # synthetic member rows: total = sum of means, min = min of means (not mean of mins)
def test_joint_reference_tie_order():        # equal totals -> honest-max before abstain before joint twin
def test_joint_twin_forces_clip():
```

- [ ] **Step 2: Run** `uv run pytest tests/test_objectives_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement `sim/objectives_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_objectives_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add sim/objectives_v2.py tests/test_objectives_v2.py && git -c commit.gpgsign=false commit -m "welfare (W0, W1 feasibility-first) and coalition (total, worst member, joint reference) objectives"`

### Task 10: Manifest, priority, and cuts

**Files:**
- Create: `experiments/revision-v2-manifest.yaml`, `sim/manifest_v2.py`, `tests/test_manifest_v2.py`

**Interfaces:**
- Produces: `manifest_v2.cells(cuts: int = 0) -> list[dict]` (design 8.1 blocks; each cell `{"id", "block", "market", "rule", "family", "objective", "c", "schedule", "rho", "priority"}`); `manifest_v2.doublings() -> list[str]` (132 cell ids, design 6.5); `manifest_v2.cross_evaluations() -> list[tuple[str, str]]` (14); `manifest_v2.CUT_ORDER` (design 8.2 evaluation cuts 1 to 4); `manifest_v2.priority(cell) -> int` (Q4 and Q1 cells 0, Q2 1, Q3 2, rest 3). `manifest_v2.effective(cuts: int = 0, h4_excluded: bool = False) -> list[dict]` (the cells after the cuts in force and an H4 exclusion); `manifest_v2.required(context: str, cuts: int = 0, h4_excluded: bool = False) -> list[str]` (every record id the freeze of that context needs, including references, joint references, envelope choices, and the fixed-attack bank); `manifest_v2.bank_rules(context: str, family: str, cuts: int = 0) -> list[str]` (the matched rules of that context and family in the effective manifest).

- [ ] **Step 1: Write the failing tests**

```python
def test_counts():            # 374 cells, 126 on the X7-SC knob space, 132 doublings, 14 cross-evaluations
def test_block_counts():      # 168, 84, 56, 3, 16, 32, 15
def test_every_rule_has_menu_searches():   # every (market, rule) has D2+H3 and X7-SC profit cells
def test_cuts_in_order():     # cuts=1 removes exactly the 48 whole-system cells on fresh markets (4 rules x 2 families x 6), listed by id;
                              # then H4 fresh (24), D2 fresh (24), C*/S0 fresh (12); retained ids asserted after each cut
def test_priority():
def test_effective_and_required():   # h4_excluded removes the 28 H4 cells and their records; required(context) lists references for every rule with menu searches
def test_bank_rules():              # headline@rho1 -> the 5 repair rules; fresh market with cuts=4 -> 11; otherwise 12
```

- [ ] **Step 2: Run** `uv run pytest tests/test_manifest_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement the YAML and `sim/manifest_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_manifest_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add experiments/revision-v2-manifest.yaml sim/manifest_v2.py tests/test_manifest_v2.py && git -c commit.gpgsign=false commit -m "v2 manifest: 374 cells, 132 doublings, 14 cross-evaluations, priority and cut order"`

### Task 11: The v2 runner and the H4 loader

**Files:**
- Create: `scripts/revision_v2.py`, `sim/records_v2.py`, `sim/h4_loader.py`, `tests/test_revision_v2.py`, `tests/test_h4_loader.py`

**Interfaces:**
- Consumes: Tasks 1 to 10 (the effective manifest of Task 10 defines the required records and bank groups); `sim.reference.twin_search`, `reference_candidates`, `select_reference`, `evaluate_gain`; `sim.search.cma_search`, `Objective`; `sim.cell.Cell`, `SeedCache`; `sim.positions.positions`; `sim.sealed.bundle_hash`-style hashing.
- Market and context: `revision_v2.market(label: str, root: str, rho: float = 0.2) -> dict` (`cfg` calibrated, `focal` at the median position, `seeds_train` 1000-1004, `seeds_val` 2000-2019, `seeds_eval` from `instances.eval_seeds` or, under `--dev`, dev-val; `context` = `"<label>@rho<rho>"`). Every record path and key uses the context, so headline rho = 0.2 and rho = 1 never collide.
- Jobs: `revision_v2.job(market: dict, rule: str, family: str, objective: str = "profit", c: int | None = None, schedule: str | None = None, smoke: bool = False) -> dict`.
- Stages, in order: `search`, `reference`, `dependent`, `freeze`, `evaluate`, `cross`, `doubling`; `revision_v2.run(stage: str, jobs: list[dict], out: Path, workers: int = 1) -> dict`.
- Search adapters (frozen functions are not edited): `search_family(cell, family, cache, settings, twin, extra_incumbents: dict) -> SearchResult` calls `cma_search` with incumbents `twin_best`, `honest_point`, and the extras; X7-SC cells pass `embedded_h3` = `embed_h3` of the same rule and context's D2+H3 attack (the X7-SC search therefore runs after that D2+H3 search); `controls(objective, family) -> list` uses `x7.corner_vectors` for X7-SC and `family.corners()` otherwise.
- Records: `records_v2.write(path, rec)` writes atomically (temporary file, fsync, rename); `read` returns `None` for a missing or unparsable file; `validate(job, stage, rec, upstream)` checks provenance (`git_commit`, `runner_sha256`, `cfg_sha256`, `salt_sha256`, `root`, `seeds_*`, `budget`, `rule_params_sha256`) and the hashes of its upstream records. Candidates serialise as `{"name", "family", "T", "L", "knobs"}` and reconstruct through the family registry with those constants.
- Reference: per rule and context, the menu is abstain, honest-max, and the twin, projection, archive, and bank candidates of the rule's D2+H3 and X7-SC search records, de-duplicated by (family, exact key) in the registered category order, D2+H3 before X7-SC within a category. Bank candidates: the projected best attacks of the same family's searches of the other matched rules that the effective manifest (Task 10, with the cuts in force) contains in the same context (the five repair rules at rho = 1; the twelve, or eleven after cut 4 on fresh markets, otherwise); tuned and reference rules use their own two searches only. Writes `reference/<context>/<rule>.json`.
- Dependent: W1 searches (after the rule's reference), then per coalition cell the joint-twin search, the joint-reference freeze (`joint_reference/<context>/<rule>_c<c>_<schedule>.json`), then the `total` and `min` searches.
- Freeze: `freeze/<context>.json` is written only if every record that the effective manifest (Task 10, with the cuts in force) requires for that context exists, validates, and has an up-to-date upstream chain, including envelope family choices (design 9.3 Q3, chosen on training gains) and the fixed-attack bank (design 6.6); the freeze lists every record hash. `evaluate` and `cross` refuse, before creating any episode, unless the context's freeze exists, every listed hash matches the file on disk, and the same completeness check (effective manifest, required record set, provenance, current upstream chain) passes again at acceptance.
- Doubling: continues the registered search with as many new restarts as registered (restart seeds offset by the registered restart count), merges the original and new archives, and reports, in the objective's units, the attack change, the reference change (re-selection from the merged menu, diagnostic only), the W1 feasibility transition, and the label `incomplete` when a change reaches 0.005; it never writes into frozen records.
- Salt: with `--root`, the CLI writes `out/salt.hex` from `instances.identity_salt_hex(root)` and sets `os.environ["TOUCHSTONE_IDENTITY_SALT"]` to it before any episode (the pod wrapper's `unset` happens in the parent shell, before the process starts).
- H4: the bundle's `h4/family.py` exports `make_family(T: int, L: int) -> Family` (the brief to the sealed session states this contract). `h4_loader.load(bundle_dir: Path, expected_sha256: str) -> H4Source | Excluded` verifies the bundle hash over `h4/family.py`, `h4/containment.md`, `h4/check.json`, imports the module by absolute path, calls `make_family(200, 10)` and `make_family(100, 20)`, and checks each result is a `Family` named `H4` with `clip` last and bounds for every non-binary knob; `H4Source.family(T, L) -> Family` binds the constants for a cell, and record reconstruction calls it with the stored T and L; any failure returns `Excluded(reason)`, which the runner records and which removes H4 cells from the effective manifest.
- CLI: `uv run python scripts/revision_v2.py --stage S --select GLOB --out DIR [--workers N] [--dev] [--smoke] [--root HEX] [--h4 DIR --h4-sha HEX]`. Every v2 CLI writes all its outputs under `--out` (the pod launcher pulls only that directory and the logs); files are promoted into `experiments/v2/` by the operations plan after they are pulled and validated.

- [ ] **Step 1: Write the failing tests** (all `--smoke` on `dev0`: 1 restart x 16 evaluations, 1 training seed, 2 evaluation seeds)

```python
def test_job_provenance_and_context():               # contexts dev0@rho0.2 and dev0@rho1 give distinct record paths
def test_reference_menu_is_union_of_two_searches():  # candidates carry family D2+H3 or X7-SC (plus abstain, honest-max); order by category then family
def test_reference_survives_resume():                # reconstruction from JSON gives the same candidate factories (same fingerprint on one seed)
def test_bank_group_follows_effective_manifest():    # rho = 1 context: 5 rules; cut 4 on a fresh market: 11; default: 12
def test_x7_uses_769_controls_and_embedded_incumbent():   # evaluated control vectors == 769 per training seed; incumbents include embedded_h3
def test_dependent_stage_requires_reference():
def test_freeze_refuses_incomplete_manifest():       # a context missing one required record: no freeze written
def test_evaluate_refuses_before_final_freeze():     # zero evaluation-seed episodes run (SeedCache.runs unchanged)
def test_freeze_hash_mismatch_refuses():
def test_accept_refuses_supplied_incomplete_freeze():   # a hand-written freeze with valid hashes but a missing required record: zero episodes
def test_accept_refuses_stale_upstream():              # a reference rewritten after the freeze's search record changed: zero episodes
def test_truncated_record_is_rerun():
def test_doubling_reports_and_labels():              # stub objectives: change 0.005 -> incomplete; 0.0049 -> complete; W1 None -> feasible -> incomplete
def test_doubling_executes_full_budget_new_seeds():   # instrumented cma_search: restart seeds start at the registered restart count,
                                                     # evaluations == the registered budget, archives merged (old keys kept)
def test_doubling_reference_only_change():           # attack unchanged, reference profit changes: reported separately, attack change 0
def test_doubling_does_not_touch_frozen_records():
def test_cross_evaluation_matrix_shape():            # 8 x 8 per context and family
def test_resume_skips_valid_and_refuses_foreign():
def test_fresh_root_installs_salt_in_process():      # with TOUCHSTONE_IDENTITY_SALT unset in the environment, --root changes a replacement
                                                     # profile's trajectory relative to --dev (salt reaches the episode)
def test_cli_accepts_pod_arguments():                # main(["--stage", "search", "--select", "x", "--workers", "2", "--out", tmp, "--dev", "--smoke"]) exits 0
# tests/test_h4_loader.py (synthetic bundles in tmp_path only)
def test_h4_loads_valid_bundle():
def test_h4_hash_mismatch_excluded():
def test_h4_import_error_excluded():
def test_h4_interface_violation_excluded():          # clip not last, missing bounds, or no make_family
def test_h4_binds_constants_and_resumes():           # synthetic bundle: episode at T = 100, L = 20 uses those constants; reconstruction from a record gives the same fingerprint
```

- [ ] **Step 2: Run** `uv run pytest tests/test_revision_v2.py tests/test_h4_loader.py -q`; expected FAIL.
- [ ] **Step 3: Implement `sim/records_v2.py`, `sim/h4_loader.py`, and `scripts/revision_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_revision_v2.py tests/test_h4_loader.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add scripts/revision_v2.py sim/records_v2.py sim/h4_loader.py tests/test_revision_v2.py tests/test_h4_loader.py && git -c commit.gpgsign=false commit -m "v2 runner: contexts, common reference menu, dependency and complete freeze, cross-evaluation, doubling, in-process salt, H4 loader"`

### Task 12: Tuning v2 (comparator selection, whole systems, fixture searches)

**Files:**
- Create: `scripts/tune_v2.py`, `tests/test_tune_v2.py`

**Interfaces:**
- Consumes: `rules_v2.make_rule`, `credibility.SELECTION_GRID`, `x7.x7_family`, `revision_v2.search_family` and `controls` (Task 11), the inner and full search settings, `instances.dev_markets`, the headline market.
- Produces: `tune_v2.margin(eff, gain) -> float` and `tune_v2.objective(margins_by_market: dict) -> float` (min over markets of min over D2, D2+H3, X7-SC; design 4.1); `tune_v2.select_comparator(markets, log_dir, inner, full) -> dict` (12 configurations, top 2 rechecked, writes `<out>/comparator.json`); `tune_v2.tune_system(name, markets, log_dir, inner, full, cred=None) -> dict` (16 configurations, top 2 rechecked, writes `<out>/tuned_<name>.json` with total episode counts); `tune_v2.fixture_searches(markets, log_dir, inner, cred) -> dict` (C*/S2 at the fixed pair: D2, D2+H3, X7-SC inner searches on each market, 9 searches, and its development reference; writes `<out>/fixture_cstar_s2.json`); development references from {D2, D2+H3, X7-SC} (design 6.4); CLI `--select comparator|B3-t|R3-t|R4-t|C*-t|fixtures --markets headline,dev0,dev1 --out DIR [--workers N] [--smoke]` (logs under `<out>/log/`); C*-t reads the comparator from `--comparator PATH`.

- [ ] **Step 1: Write the failing tests**

```python
def test_objective_is_min_over_markets_and_families():
def test_grid_sizes():                    # comparator 12, every whole system 16
def test_ties_by_grid_order():
def test_recheck_top2_on_dev_val():
def test_c_t_keeps_comparator_variant():  # C*-t tunes tol and L only; variant, K, M frozen from comparator.json
def test_fixture_searches_count():        # 9 searches and one development reference for C*/S2
def test_smoke_run_writes_logs():         # --smoke on dev0 only
def test_cli_accepts_pod_arguments():     # main(["--select", "comparator", "--markets", "dev0", "--smoke", "--workers", "2", "--out", tmp]) exits 0, outputs under tmp
```

- [ ] **Step 2: Run** `uv run pytest tests/test_tune_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement `scripts/tune_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_tune_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add scripts/tune_v2.py tests/test_tune_v2.py && git -c commit.gpgsign=false commit -m "tuning v2: common objective, comparator selection, whole-system tuning, C*/S2 fixture searches"`

### Task 13: Coverage and calibration v2

**Files:**
- Create: `sim/calibration_v2.py`, `scripts/coverage_v2.py`, `tests/test_calibration_v2.py`

**Interfaces:**
- Consumes: Task 8 functions; `instances.coverage_pool`; Task 12's frozen development attacks and references (promoted copies under `experiments/v2/`: `comparator.json`, the `tuned_*.json` logs at the fixed pair, `fixture_cstar_s2.json`).
- Produces: `calibration_v2.PROFILES` (the 14 profiles of design 9.5, in a fixed order: F000 D2+H3 attack; F111, C*, R4, C*/S2 D2+H3 and X7-SC attacks; the five references); `calibration_v2.build_pool(market: dict, attacks: dict, refs: dict, seeds: list[int]) -> dict` (per seed, every profile run on that seed's draws, so rows align by seed); `calibration_v2.strata(pools: dict[str, list[int]], branch: str) -> list[list[int]]` (branches `three20k`, `two20k`, `two10k`; consecutive blocks by derivation index); `calibration_v2.endpoints(family: str, branch: str) -> list[dict]` (Q1 32; Q4 36 with three markets, 24 with two; each with `alpha_e`, side, step, fixture) and `calibration_v2.denominator(family) -> int` (32 or 36 in every branch); `calibration_v2.miss(rows, endpoint, kappa, replications, seed) -> int`; `calibration_v2.select_kappa(family, fixtures, branch, seed) -> float | None` (10,000 replications; the largest kappa in (1, 1/2, 1/4) with every endpoint's observed miss rate <= alpha_e); `calibration_v2.validate(family, kappa, fixtures, branch, seed) -> dict` (20,000 replications with new resampling seeds; admitted only if every endpoint's Clopper-Pearson upper bound at 1 - 0.01 / denominator is <= alpha_e); `scripts/coverage_v2.py --pools | --select | --validate --branch B --out DIR [--workers N]` writing `<out>/coverage.json`.

- [ ] **Step 1: Write the failing tests**

```python
def test_pool_rows_align_by_seed():                 # every profile's row i comes from seed i (draws equal), 14 profiles exactly
def test_strata_branches_sizes_and_remainders():   # 2 x 10000; 3 x 6666 (2 dropped); 3 x 3333 (1 dropped)
def test_endpoint_counts_by_branch():               # Q1 32 always; Q4 36 (three markets) or 24 (two); denominators 32 and 36
def test_select_largest_passing_kappa():           # constructed misses: kappa 1 fails, 1/2 passes -> 0.5 (not 0.25)
def test_select_none_when_all_fail():
def test_validation_rejects_if_any_endpoint_fails():
def test_validation_uses_independent_seeds():
```

- [ ] **Step 2: Run** `uv run pytest tests/test_calibration_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement `sim/calibration_v2.py` and `scripts/coverage_v2.py`** (resample indices shared across a fixture's statistics; vectorised numpy).
- [ ] **Step 4: Run** `uv run pytest tests/test_calibration_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add sim/calibration_v2.py scripts/coverage_v2.py tests/test_calibration_v2.py && git -c commit.gpgsign=false commit -m "coverage v2: aligned 14-profile pools, fixture branches, endpoints, kappa selection and independent validation"`

### Task 14: Benchmark and pod entry

**Files:**
- Create: `scripts/benchmark_v2.py`, `tests/test_benchmark_v2.py`
- Modify: `results/pods/explore_pod.sh` only through its existing `SCRIPT` and `ROUT` environment overrides (no edit; documented in the benchmark's docstring)

**Interfaces:**
- Produces: `benchmark_v2.KINDS` (one cell each: headline D2+H3 profit, X7-SC profit, W1, coalition total, inner tuning search, one coverage fixture replication batch, one cross-evaluation row, one doubling); `benchmark_v2.cost_table(timings: dict, usd_per_core_hour: float) -> dict` reproducing design 8.2's rows from measured seconds; CLI `--run --out DIR [--workers N] [--dry-run]` (measures; `--dry-run` parses, builds the jobs, and exits without episodes) and `--table TIMINGS.json` (prints the recomputed table, flags any cap exceeded: development 12 USD, evaluation 40 USD, approval above 40 USD total).

- [ ] **Step 1: Write the failing tests**

```python
def test_cost_table_reproduces_design_units():   # with timings equal to the design's unit assumptions, totals are 233.6 and 868.8 units within rounding
def test_flags_caps_and_approval():
def test_cli_accepts_pod_arguments():            # main(["--run", "--dry-run", "--workers", "2", "--out", tmp]) exits 0
```

- [ ] **Step 2: Run** `uv run pytest tests/test_benchmark_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement `scripts/benchmark_v2.py`.**
- [ ] **Step 4: Run** `uv run pytest tests/test_benchmark_v2.py -q && uv run pytest -q`; expected PASS for both (the whole suite green).
- [ ] **Step 5: Commit** `git add scripts/benchmark_v2.py tests/test_benchmark_v2.py && git -c commit.gpgsign=false commit -m "benchmark v2: per-kind timings and the recomputed cost table with caps"`

---

## After this plan

A second plan (operations) covers, in design 11 order: the sealed H4 session, the paid benchmark and the author's cost approval, comparator selection and tuning on pods, coverage, protocol v2 and its lock, the draw, the evaluation, the report, the artifact, and the paper revision. It is written after this plan's final review, against the code as built.
