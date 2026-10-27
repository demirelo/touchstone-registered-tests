# Revision program, Part A2: design draft 7 in code (Implementation Plan, version 2)

Status: version 2 answers round 1 (`docs/revision/roster/{sol,astra}-a2-plan-r1.md`, both reject); dispositions at the end.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Part A code on main `fee49c9` (built to design draft 6) to design draft 7, so that Part B of the operations plan runs the accepted design.

**Architecture:** Twelve tasks, each test first against the draft-6 code, on development data only (no pods, no paid calls). The order follows the dependencies: the manifest and rule set first (every later task reads them), then the families and the comparator, then the runner stages (coalition order, menus, H4, records), then decisions, coverage, tuning, cost, and report, then the operations-plan and H4-brief documents, and last an executable test of the revised operations sequence. A whole-branch review by Sol high and Astra high closes Part A2; its reviewed head becomes `code_commit` for Part B.

**Tech Stack:** Python 3 with uv, numpy, scipy 1.18.1 (pinned in `uv.lock`), cma, pytest.

**Spec:** `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 7, accepted in round 9; "design"). Section 14's "Code" column is the scope of this plan. The operations plan `docs/superpowers/plans/2026-10-25-revision-operations.md` (version 9) and its rulings `docs/revision/operations-rulings-2026-10-27.md` stay in force except where this plan changes them (Task 11).

## Global Constraints

- No paid API calls; no pods. Development data only: seeds dev-train 1000-1004, dev-val 2000-2019, calibration 4000-4019, coverage pools in [40,000,000, 60,000,000); root "dev-20261022". Evaluation seeds [30,000,000, 40,000,000) are never used.
- Frozen files stay byte-identical to `2a288f5` (`tests/test_frozen_files.py`). Registered files of the first evaluation (`experiments/locked.yaml`, `sealed/`, its records) are never changed; `sealed/` and any `sealed2/` are never read.
- Fixed pair tol = 0.16, L = 10 (design 3.1). rho = 0.2 except the repair block (rho = 1).
- Counts this plan must produce (design 8.1, 8.2, 6.5, 9.5): **287 search cells** (85 on the X7-SC knob space, 21 H4), **3 diagnostic cells** (no search), **98 doubling checks**, **14 cross-evaluations**, **8 coverage profiles**, **Q1: 2 tests, 8 endpoints, m = 8**; Q4 unchanged (36 endpoints).
- Rule set (design 3.5): matched F000..F111, C*, C*/S0; core F000, F111, C*; whole systems B3-t, R3-t, C*-t; B2 headline reference; R4 and C*/S2 only in the rho = 1 repair block. R4-t is removed everywhere.
- Statuses (design 6.5): **missing** (not run, cut, refused sample, nonfinite statistic, no finite candidate, H4 load failure) versus **search-flagged** (completed, doubling check over 0.005).
- Commits unsigned (`git -c commit.gpgsign=false`), ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the author signs. Whole suite `uv run pytest -q`; touched modules' suites after each task. Code style as the surrounding code.

## Review Focus

1. **Draft-6 records on disk after the change** (R4 cells at rho 0.2, per-schedule joint references, 14-profile pools). The resume rule must refuse them as foreign, never reuse them. Pinned by Task 1 `test_draft6_cell_ids_are_foreign` and Task 5 `test_per_schedule_joint_records_are_refused`.
2. **A coalition group whose reference steps are incomplete or out of order.** G_min must not run before the preliminary reference, evaluation must not run before the final reference and rescoring. Pinned by Task 5 `test_coalition_order_is_enforced`.
3. **An H4 bundle outside the envelope** (more than 15 knobs, no projection, unbounded knob). It is excluded at load with the reason, and the runner never enumerates `Family.corners()` for it. Pinned by Task 7 `test_h4_outside_envelope_is_excluded` and `test_h4_controls_are_bounded`.
4. **The distinct-rule check at the generator's ends** (total capacity K = 40 and K = 80; rho = 1). Pinned by Task 1 `test_distinct_rule_bound_at_generator_ends`.
5. **A fresh-market secondary system with a stray X7-SC record.** Its menu must stay D2+H3-only and equal for B3-t, R3-t, C*-t. Pinned by Task 6 `test_fresh_secondary_menu_ignores_x7_records`.

---

## Task 1: Manifest, rule set, distinct-rule check, question map (D1, D17, D10 cells, D4 cells)

**Files:** Modify `experiments/revision-v2-manifest.yaml`, `sim/manifest_v2.py`, `sim/rules_v2.py`. Tests `tests/test_manifest_v2.py`, `tests/test_rules_v2.py`.

**Interfaces — Produces:**
- Manifest blocks (design 8.1): `matched` {F000..F111, "C*", "C*/S0"} x {D2+H3, X7-SC} x all; `extras` {F000, F111, "C*"} x {D2, X5-AG/v2, H4} x all; `tuned` {B3-t, R3-t, "C*-t"} with `families_by_market: {headline: [D2+H3, X7-SC], fresh: [D2+H3]}`; `reference` unchanged; `welfare` {F000, F111, "C*"}; `coalition` {F000, F111, "C*"} x X6-SE/v2 x c {2, 5} x {synchronised, staggered} x {total, min}; new `coalition_roles` {F000, F111, "C*"} x X8-DB x c 2 x schedule `roles` x {total, min}; `repair` unchanged (rho 1); new `diagnostic` {F000, F111, "C*"} x family `HR1` x objective `diagnostic` x headline. Doublings: headline matched (10 rules x 2), welfare, coalition, coalition_roles; fresh {F000, F111, "C*"} x {D2+H3, X7-SC}.
- `sim/manifest_v2.py`: `Q1_Q4_RULES = ("F000", "F111", "C*")`; `MATCHED` without "C*/S2" and "R4"; `cells()` returns 287 search cells plus 3 `diagnostic` cells (block `diagnostic`, excluded from `doublings()`, `bank_rules()`, and the reference requirements); coalition ids keep the `|c<c>_<schedule>` suffix (`roles` for X8-DB).
- `QUESTIONS: dict[str, dict]` with keys `Q1, Q2, Q3, Q4, repair, whole` mapping to `{"cells": [...ids], "checks": [...ids]}` exactly as design 8.1a; `question_cells(name, cuts=0, h4_excluded=False) -> dict`.
- `distinct_rule_problems(cells: list[dict], a_tot: dict[str, int]) -> list[str]` (design 3.4): for each block and context, two rules conflict if they have the same selection descriptor and the same pacing schedule (`reserve = min(J L, A_tot)` for S1, `min(J L, A_tot // 2)` for S2, spread for S0) on that context's `a_tot`. `cells()` raises on any problem with the headline calibration (`experiments/calibration.json`).
- `sim/rules_v2.py`: `MATCHED`, `CORE = ["F000", "F111", "C*"]`, `TUNED = ["B3-t", "R3-t", "C*-t"]`, and `FIXED = MATCHED + ["R4", "C*/S2"]` (rules at the fixed pair, whatever their block); `make_rule("R4-t")` raises `ValueError`. `scripts/revision_v2.rule_spec` uses `FIXED` (not `MATCHED`) to give the fixed pair, so the repair rules never look for tuned parameters.
- Diagnostic cells are excluded from `required()` before the freeze and from `stage_upstream` for search; a diagnostic evaluation requires the context's accepted freeze record.

- [ ] **Step 1: failing tests.** `test_counts_draft7`: `len([c for c in cells() if c["block"] != "diagnostic"]) == 287`, X7-SC cells 85, H4 cells 21, diagnostic cells 3, `len(doublings()) == 98`, `len(cross_evaluations()) == 14`. `test_no_r4_or_cstar_s2_at_rho02`: no cell with rule in {"R4", "C*/S2"} and rho 0.2; both present at rho 1. `test_no_r4t`: "R4-t" in no cell and `make_rule("R4-t")` raises. `test_tuned_fresh_d2h3_only`: tuned cells on fresh markets have family D2+H3 only. `test_distinct_rule_bound_at_generator_ends`: with `a_tot` from n_FB = 200 min(50, K) for K = 40 and K = 80 at rho 0.2 (2,000 and 2,500), a manifest that puts R4 beside F111 in one block is refused; at rho 1 (A_tot 400 and 500) it is accepted. `test_draft6_cell_ids_are_foreign`: `"headline@rho0.2|R4|D2+H3|profit"` and `"headline@rho0.2|C*/S2|X7-SC|profit"` are not in `cells()` and `scripts.revision_v2.check_record` refuses a record with either id. `test_question_map`: Q1 cells = F111 and C* x 2 families x 6 fresh (24) and checks the same 24; Q4 = F000 and F111 x D2+H3 x 6 fresh (12); Q3 includes the H4 cells and the diagnostic cells. `test_repair_rules_construct`: with a params file holding only `cred` and the three tuned systems, `rule_spec` and `rule_factory` build every job of the rho = 1 block (R4, C*/S2 included). `test_diagnostic_after_freeze`: on a smoke headline context, freeze succeeds without any diagnostic search record, a diagnostic evaluation before the freeze is refused, and after it the diagnostic evaluates and `verify` accepts it.
- [ ] **Step 2:** run them; expected FAIL (287 vs 374; R4 present; no `QUESTIONS`).
- [ ] **Step 3:** implement as the Interfaces block says.
- [ ] **Step 4:** `uv run pytest tests/test_manifest_v2.py tests/test_rules_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 1: draft-7 manifest and rule set (R4 and C*/S2 at rho 1 only, no R4-t, X8-DB and diagnostic cells, distinct-rule check, question map)".

## Task 2: C-boinc comparator (D7)

**Files:** Modify `sim/mechanisms/credibility.py`. Test `tests/test_credibility.py`.

**Interfaces — Produces:** `VARIANTS = ("thr", "mem", "taper", "boinc")`; `boinc_weight(p: int) -> float` = 1.0 if p < 10 else 1.0 / p; `select_credibility("boinc", ...)` uses the exponential race of C-taper with `boinc_weight`; `SELECTION_GRID` = C-thr K {2, 6, 12, 24}, C-mem (K, M) {(2, 20), (2, 50), (6, 20), (6, 50)}, C-taper K {2, 6, 12}, and `{"variant": "boinc", "K": 10, "M": None}` (12 entries; K is recorded as 10 for the threshold and is not tunable). `Credibility("boinc", 10, ...)` with any other K raises.

- [ ] **Step 1: failing tests.** `test_boinc_weight`: weights 1 at p 0 and 9, 0.1 at p 10, 0.05 at p 20. `test_boinc_selection_race`: on a fixed `jobs_by_identity` and audit keys, the k selected jobs are the k smallest `-ln(key) / boinc_weight(p)`, ties by job index. `test_selection_grid_draft7`: 12 entries, no taper K 24, one boinc entry. `test_boinc_k_fixed`: `Credibility("boinc", 6, 0.16, 10)` raises.
- [ ] **Step 2:** run; expected FAIL (unknown variant).
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_credibility.py tests/test_tune_v2.py -q`; expected PASS (update `test_tune_v2` grid expectations).
- [ ] **Step 5:** commit "A2 task 2: C-boinc replaces C-taper K 24".

## Task 3: X7-SC with reset-or-wait and the exposure gate (D3)

**Files:** Modify `sim/policies/x7.py`. Test `tests/test_x7.py`.

**Interfaces — Produces:** `KNOBS = ("u0", "m0", "s", "d", "r", "w", "k_F", "k_T", "a_F", "n_P", "h_R", "a_R", "e_P", "lambda", "clip")` (15); `X7Policy(..., h_R, a_R, e_P, lam, clip, T, L)` with domains a_R in [0, T], e_P in [0, 1]; state `p_own` (design 5.2): batch update after each round's audit results of the current identity, 0 on any failure in that round, else plus the passes; cleared on exit. Round order as design 5.2 steps 1-6: failure trigger needs `T - t > h_R` and `t - c < a_R`; the voluntary trigger is not evaluated in a round where the failure trigger fired, nor in a round after a failure rejected by the age gate, nor while the identity is banned (`history.banned_until[-1] > t - 1`), until the identity has served again; fresh phase if `(t - c) < a_F` or `p_own < n_P` or (window [max(c, t - L), t) has served >= 1 and audited / served > e_P). `embed_h3(knobs, T)` sets a_R = T and e_P = 1 in addition to the draft-6 values. `x7_corners` uses `Sobol(d=15, ...)`; `X7_CORNER_COUNT: int` is the distinct count the build computes with scipy 1.18.1, written as a constant and asserted.

- [ ] **Step 1: failing tests.** `test_x7_knobs_15`. `test_embedding_draft7`: identical round records to D2+H3 for x = 0 and x = 1 on F000, F111, C* (and every common-grid rule already in the draft-6 test), 5 seeds. `test_age_gate_waits`: a scripted history with a failure at age >= a_R gives no exit, and no voluntary exit during the ban even when audited / served > lambda; after the identity serves again the voluntary trigger fires. `test_p_own_batch_update`: a round with passes and one failure gives 0; a round with 3 passes adds 3. `test_exposure_gate`: same age and p_own, audited / served above e_P gives the fresh multiplier, below gives the established one; e_P = 1 never forces fresh. `test_corner_count_recorded`: `len(corner_vectors(x7_family(200, 10))) == X7_CORNER_COUNT`.
- [ ] **Step 2:** run; expected FAIL (13 knobs).
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_x7.py tests/test_policies_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 3: X7-SC reset-or-wait, exposure gate, p_own (15 knobs)".

## Task 4: X8-DB family and the generalised coalition objective (D4)

**Files:** Create `sim/policies/x8.py`. Modify `sim/families_v2.py`, `sim/objectives_v2.py`. Tests `tests/test_x8.py`, `tests/test_objectives_v2.py`.

**Interfaces — Produces:**
- `X8_KNOBS = ("n_D", "u_D", "w_D", "u_B", "m_B", "s_B", "w_B", "g_B", "clip")`; bounds n_D [1, 2L], u_D [0, 1], w_D [0, 2], u_B [0, 1], m_B [0, 1], s_B [0, 0.3], w_B [0, 2]; g_B and clip binary. `x8_family(T: int, L: int) -> Family` (name "X8-DB"); `Family.project` sets clip = 1 only.
- `X8Pair(knobs, T, L)`: a shared coordinator holding the decoy's identity state; `x8_members(knobs, T, L) -> tuple[policy, policy]` returns (beneficiary, decoy) policies that share it. Timing (design 5.2): in round t the coordinator first decides the decoy's replacement (failure in t - 1, or `t - c_D >= n_D`, real comparison; c_D = t after any replacement), then the gate from the offering decoy identity's age; the result is independent of which member's `act` the harness calls first (the coordinator computes round t once).
- `member_factories(family_name: str, knobs: dict, members: tuple, staggered: bool | None, T: int, L: int) -> list[callable]` in `sim/objectives_v2.py`, covering "X6-SE/v2" (existing `x6v2_member`) and "X8-DB". `CoalitionObjective(..., family_name: str = "X6-SE/v2", ...)` uses it; X8-DB requires `len(members) == 2`.
- `sim/families_v2.family_for("X8-DB", T, L)`.
- `ProfileDescriptor`: a JSON object `{"kind": "honest_max" | "abstain" | "knobs", "family": str | null, "schedule": "synchronised" | "staggered" | "roles" | null, "knobs": dict | null}`; `profile_factories(desc, members, T, L) -> list[callable]` rebuilds the members' policies from it. Every joint reference, preliminary reference, and coalition winner record stores one.

- [ ] **Step 1: failing tests.** `test_x8_schedule_real_nd`: with n_D = 2.5 the decoy replaces at ages 3, 3, ...; a failure at age 1 replaces and restarts the clock. `test_x8_gate_at_replacement_boundary`: in the round the decoy replaces, the gate sees age 0 (< L, so the beneficiary shades when g_B = 1). `test_x8_call_order_independent`: round records identical when the members' order in the provider list is swapped. `test_x8_projection_keeps_decoy`: `x8_family(200, 10).project(k)` changes only clip. `test_x8_members_read_only_member_histories`: the coordinator receives only the two members' `ProviderView` histories. `test_coalition_objective_x8`: total and min computed from the two members' rows against a given reference.
- [ ] **Step 2:** run; expected FAIL (no module).
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_x8.py tests/test_objectives_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 4: X8-DB decoy and beneficiary family; coalition objective by family".

## Task 5: Six-step coalition reference order (D5)

**Files:** Modify `scripts/revision_v2.py` (`coalition_prereqs`, `stage_dependent`, `expected_upstream`, `check_record`, `_waves`, `required` use), `sim/objectives_v2.py` (`joint_reference`), `sim/manifest_v2.py` (`required`). Test `tests/test_revision_v2.py`.

**Interfaces — Produces:** per coalition group `(context, rule, c)` (tag `{rule}_c{c}`; X6-SE/v2 schedules and X8-DB share it), records in order: `joint_twin/{ctx}/{tag}_synchronised`, `joint_twin/{ctx}/{tag}_staggered` (step 1); the G_tot cells (step 2, no reference input); `joint_reference_pre/{ctx}/{tag}` (step 3: menu all honest-max, all abstain, twin sync, twin staggered, then the truthful projections of the step-2 winners and of every archive point, in search order); the G_min cells against it (step 4, the reference profile inserted as an incumbent where representable); `joint_reference/{ctx}/{tag}` (step 5: the step-3 menu plus the projections of the step-4 winners and archive points); `coalition_select/{ctx}/{tag}` (step 6: every archived G_min point rescored against the final reference on the same training seeds, plus the final reference profile where representable, score 0; the winner per G_min cell). `joint_reference(cfg, rule_factory, members, seeds, cache, menu: list[tuple[str, list[callable]]]) -> dict` takes the ordered menu. Evaluation of a G_min cell reads its winner from `coalition_select`; a G_tot cell's winner is its own search's best. The freeze order (design 6.4 step 3) requires all six steps. The coalition branches of `stage_dependent`, `stage_evaluate`, and `stage_doubling` build members through `profile_factories` and `member_factories` (Task 4), never through `x6v2_member` directly; `expected_provenance` and `check_record` use the new group tag `{rule}_c{c}`. **Doubling of a G_min cell** continues its search with the final reference: the merged archive is rescored against the final reference before the comparison, so the doubling and the frozen winner are scored against the same reference.

- [ ] **Step 1: failing tests.** `test_coalition_order_is_enforced`: G_min refuses without `joint_reference_pre`; evaluate refuses without `joint_reference` and `coalition_select`. `test_reference_menu_order`: ties broken in the stated order; projections enter in search order. `test_final_reference_can_win_gmin` (Sol round-8 case): a final reference from a step-5 projection with every archived point negative against it selects the reference profile when representable. `test_gtot_winner_unchanged_by_reference`: the G_tot winner is the same under the preliminary and final references. `test_per_schedule_joint_records_are_refused`: a draft-6 record `joint_reference/headline@rho0.2/F111_c2_synchronised` is foreign. `test_x8_shares_group_reference`: the X8-DB cells of rule F111 and c 2 use the group's `joint_reference`. `test_reload_projection_reference_and_x8_winner`: records written to disk and read back rebuild an X8-DB projection reference and an X8-DB winner whose evaluation equals the in-memory evaluation. `test_gmin_doubling_uses_final_reference`: the doubling's comparison scores equal the step-6 rescored values for archive points.
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement; `_waves` dispatches step 1 and 2 before step 3, step 4 after it, steps 5-6 after step 4.
- [ ] **Step 4:** `uv run pytest tests/test_revision_v2.py tests/test_objectives_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 5: six-step coalition reference order with rescoring".

## Task 6: Context-dependent reference menus (D1, design 6.4 exception)

**Files:** Modify `scripts/revision_v2.py` (`menu`, `merge_menu`, `expected_upstream`, `stage_reference`), `sim/manifest_v2.py` (`menu_families(ctx, rule) -> tuple[str, ...]`). Test `tests/test_revision_v2.py`.

**Interfaces — Produces:** `menu_families(ctx, rule)` returns ("D2+H3",) for B3-t, R3-t, C*-t on fresh contexts and ("D2+H3", "X7-SC") for every other rule and context with a reference. `menu` and `expected_upstream` iterate over it; the reference record carries `menu_families`; verify and the report label fresh secondary results "reduced menu (D2+H3)".

- [ ] **Step 1: failing tests.** `test_menu_families`: the three secondary systems on fresh0 give D2+H3 only; F111 on fresh0 and B3-t on the headline give both. `test_fresh_secondary_menu_ignores_x7_records`: an X7-SC record placed in the output for `fresh0|R3-t` is not read and not required; the menus of B3-t, R3-t, C*-t on fresh0 have the same families. `test_reference_completes_without_x7`: the reference and freeze stages of `fresh0|C*-t` complete with only its D2+H3 cell.
- [ ] **Step 2:** run; expected FAIL (global `MENU`).
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_revision_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 6: reduced D2+H3 reference menu for fresh-market secondary systems".

## Task 7: Defence-aware H4 with bounded controls and a timing record (D2)

**Files:** Modify `sim/h4_loader.py`, `scripts/h4_check.py`, `scripts/revision_v2.py` (`job`, `controls`), `sim/policies/x7.py` (`corner_vectors` generalised). Tests `tests/test_h4_loader.py`, `tests/test_h4_check.py`, `tests/test_revision_v2.py`.

**Interfaces — Produces:**
- `sim/h4_loader._check(fam, binary)` also refuses more than 15 knobs, a missing or non-callable `project`, and nonfinite bounds; `load` returns `Excluded(reason)` for each.
- `corner_vectors(fam: Family) -> list[dict]` works for any family: `Sobol(d=len(fam.knobs), scramble=True, seed=SOBOL_SEED).random_base2(9)`, the same bit mapping, de-duplication, all-low and all-high corners, projections (design 5.2). `revision_v2.controls` uses it for X7-SC and H4; `Family.corners()` is used for no family with more than 8 knobs (assertion).
- `revision_v2.job`: H4 gets the X7-SC evaluation budget (`E *= 2`) and the same twin search; doubling at that budget.
- `scripts/h4_check.py`: `smoke(..., rules=("F000", "F111", "C*"), ...)`; `timing(bundle, market="headline") -> dict` runs one full-budget H4 search with its bounded controls on the headline market (dev-train seeds) and returns `{"seconds": float, "episodes": int, "knobs": int, "controls": int}`; `main` writes it into `check.json` and prints `bundle_sha256`, `commit`, and the timing record (design 5.3); C* is built from the promoted `experiments/v2/comparator.json` at the defender-freeze commit.

- [ ] **Step 1: failing tests.** `test_h4_outside_envelope_is_excluded`: synthetic bundles with 16 knobs, no `project`, and an infinite bound are each excluded with the reason. `test_h4_controls_are_bounded`: a synthetic 15-knob H4 family gets at most 2 x 514 control vectors, and `Family.corners` is not called. `test_h4_budget_is_x7`: `job(..., family="H4")["budget"][1]` equals the X7-SC value. `test_h4_check_prints_timing`: `main` on a synthetic bundle (smoke budget) prints the hash and a timing record with the four fields, and `check.json` holds the same record. `test_h4_smoke_includes_cstar`.
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_h4_loader.py tests/test_h4_check.py tests/test_revision_v2.py tests/test_x7.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 7: defence-aware H4 envelope, bounded controls, X7 budget, timing record".

## Task 8: Evaluation records, diagnostic, held-out doubling, training-selected extrema (D6, D9, D10, D12, D15, D16)

**Files:** Modify `scripts/revision_v2.py` (`GAIN_FIELDS`, `stage_evaluate`, `stage_cross`, `stage_doubling`, `_welfare_record`, `_schema_problems`, `_cross_problems`, `derived_records`, `stage_freeze`, `_run_one`, `_run_cross`), `sim/objectives_v2.py`; create `sim/diagnostic_v2.py`. Tests `tests/test_revision_v2.py`, `tests/test_records_v2.py`, new `tests/test_diagnostic_v2.py`.

**Interfaces — Produces:**
- `GAIN_FIELDS` adds `served_share_attack`, `served_share_ref` (per seed: the market's served jobs divided by the first-best served jobs n_FB of that seed's first-best solution), `false_refund_focal_attack`, `false_refund_others_attack`, `false_refund_focal_ref`, `false_refund_others_ref` (refunds on failed audits of jobs whose claim did not exceed the delivered effort, per seed, normalised by S*/N). Schema checks require them finite.
- `stage_cross` writes, per attack row and rule, per-seed `profit_attack` and `profit_ref` normalised by S*/N, and gross and net efficiency; `decompose(row: dict, rule_r: str, rule_c: str) -> dict` returns per-seed `attack_term` = profit_attack(R) - profit_attack(C) and `reference_term` = profit_ref(R) - profit_ref(C), so that gain_R - gain_C = attack_term - reference_term (design 6.6); its per-rule envelope uses the training selection below.
- **Before the freeze (design 6.4 step 4):** `derived_records` writes `bank_train/{ctx}/{family}` (the 8 x 8 gains on the bank cells' dev-train seeds) and `envelope_select/{ctx}/{rule}/{family}` (the attack with the highest training gain, ties by bank order, via `envelope_rule(train_matrix, rule) -> str`), and `welfare_select/{ctx}/{rule}/{objective}` (Task 8's `select_welfare`); `stage_freeze` hashes them; `stage_cross`, `stage_evaluate` for welfare, and the report refuse without them, and evaluation-seed values never change them.
- `stage_doubling` adds `heldout`: the doubled winner evaluated on the cell's evaluation seeds against the frozen reference (the same `GAIN_FIELDS`); never written into the frozen candidate.
- Welfare: `select_welfare(records_by_family: dict) -> str` picks, per rule and objective, the family with the lower training efficiency (ties D2+H3 first); `w1_class(lower: float, upper: float) -> str` returns "supported" (lower >= 0), "contradicted" (upper < 0), else "unresolved".
- `sim/diagnostic_v2.py`: `honest_replacement(cfg, rule_factory, focal: int, seeds, replace_at: int = 50, bin_width: int = 10) -> dict` (design 6.7): per age bin of the replacement identity, the audited share of the focal's served jobs, profit per round, and false-failure refunds; the runner's `evaluate` stage handles objective `diagnostic` with no search, no reference, and no upstream.

- [ ] **Step 1: failing tests.** `test_gain_fields_draft7` (fields present and finite in an evaluate record on a smoke cell). `test_false_refund_definition`: a scripted truthful job that fails by noise counts; a shaded job that fails does not. `test_cross_decomposition_sums`: `gain_R - gain_C == attack_term - reference_term` per seed (tolerance 1e-12). `test_envelope_uses_training`: a matrix where the evaluation-best attack differs from the training-best selects the training-best. `test_selections_frozen_before_evaluation`: the freeze refuses without `bank_train`, `envelope_select`, and `welfare_select`; cross and welfare evaluation refuse without the frozen selections. `test_resume_rejects_damaged_current_records`: an evaluate, a cross, and a doubling record with current provenance but a missing draft-7 field (for example `served_share_attack`, `heldout`) are recomputed, not skipped (`_run_one` and `_run_cross` apply `_schema_problems` and `_cross_problems` in their reuse check). `test_doubling_heldout_not_frozen`: the frozen record is byte-identical before and after the doubling stage; `heldout` is present. `test_select_welfare_training` and `test_w1_class` (three cases). `test_honest_replacement_bins`: under F000 the audited share of the replacement is flat in age within sampling noise on 20 dev-val seeds and under F111 the first bin is higher than under F000 (a direction check, not a pass threshold for the program).
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_revision_v2.py tests/test_records_v2.py tests/test_diagnostic_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 8: draft-7 evaluation fields, decomposition, training-selected extrema, held-out doubling, honest-replacement diagnostic".

## Task 9: Decisions, statuses, numerical refusals (D11, D12, D13, D14, D15, D17)

**Files:** Modify `sim/decisions_v2.py`, `sim/intervals.py` (callers' finite checks), `scripts/revision_v2.py` (`verify`), `scripts/report_v2.py` (`q1`, `q2`, `q3`, status handling). Tests `tests/test_decisions_v2.py`, `tests/test_intervals_v2.py`, `tests/test_report_v2.py`.

**Interfaces — Produces:**
- `q1_category(strata_diffs, kappa, holm_reject, m=2) -> str` returning one of "R3 materially lower", "C* materially lower", "equivalent", "equivalent, direction R3 lower", "equivalent, direction C* lower", "ordered, size not established", "inconclusive", or `NO_DECISION`; d = g_C* - g_F111; I = calibrated Bonferroni interval at one-sided tail 0.05 / (2 m) x kappa; order as design 9.3.
- `q1_efficiency(eff_strata, rule_first: bool) -> str` returning "efficiency condition met" (nominal one-sided 97.5 percent lower bound of the pooled paired gross-efficiency difference >= -0.01), "efficiency loss" (upper bound < -0.01), else "efficiency non-inferiority unresolved"; `q1_better(category, efficiency) -> str | None` returns "R3 better" or "C* better" only for category 1 in that rule's favour with the condition met, labelled descriptive.
- `q2_contrasts` adds P at G = 0 and 1, G at S = 0 and 1 (design 9.3) and, for fixed attacks, the two decomposition terms.
- `sim/intervals.py`: the shared primitives `studentized_tstats`, `stratified_tstats`, `_bound_from`, and `_pvalue_from` raise `NonfiniteStatistic` (a `ValueError` subclass) if the mean, the standard error, a bootstrap statistic, the bound, or the p-value is nonfinite, so every caller (including `two_sided_pvalue` and `stratified_two_sided`, the Q1 path) is covered. `report_v2` and `decisions_v2` catch it per test: the affected decision is "not decided: missing cell" and the cell is listed missing; every unaffected result is still reported.
- **Q1 sign:** `report_v2.q1` computes d = g_C* - g_F111 per seed (the draft-6 code computes F111 - C*), and `q1_category` receives d.
- Statuses: `verify` returns `{"missing": [...], "search_flagged": [...]}`; the report marks a test using a missing cell "not decided: missing cell", labels a decision using a search-flagged cell "about the prescribed search procedure", marks Q3 for that rule and family "unanswered (search flagged)", and uses `QUESTIONS` (Task 1) for each question's dependencies. The report states that multiplicity is controlled within Q1 and within Q4 only (design 9.4).

- [ ] **Step 1: failing tests.** `test_q1_categories` (seven synthetic strata cases, one per label). `test_q1_efficiency` (met, loss, unresolved). `test_q1_better_needs_category1_and_condition`. `test_q2_conditional_contrasts`. `test_nonfinite_statistic_refused` (a sample whose bootstrap statistics overflow raises). `test_missing_vs_flagged_statuses`: a missing Q1 cell gives "not decided: missing cell"; a flagged one keeps the decision with the label and makes Q3 for that rule and family unanswered. `test_multiplicity_statement` in the Markdown. **Report integration tests** (built from synthetic rule records on disk through `report_v2.build` and `markdown`): `test_report_q1_sign_both_directions` (records with C* gain above F111 by 0.08 give "R3 materially lower"; the reverse gives "C* materially lower"); `test_report_q1_efficiency_and_tradeoff_fields` (efficiency label and the Q1 side fields in JSON and Markdown); `test_report_q2_decomposition_per_market_and_headline`; `test_report_envelope_and_welfare_training_selected` (opposite training and evaluation rankings report the training choice); `test_report_w1_contradicted`; `test_report_q3_reduced_after_h4_exclusion`; `test_report_nonfinite_withholds_only_affected` (an overflowing Q1 test is withheld, the other Q1 test and Q4 still decided).
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_decisions_v2.py tests/test_intervals_v2.py tests/test_report_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 9: Q1 categories and efficiency condition, conditional contrasts, two statuses, nonfinite refusals".

## Task 10: Coverage, tuning, promotion, and cost model (D1, D14, D18, design 5.3 cost after H4)

**Files:** Modify `sim/calibration_v2.py`, `scripts/coverage_v2.py`, `scripts/tune_v2.py`, `scripts/promote_v2.py`, `scripts/benchmark_v2.py`, `scripts/lock_v2.py`. Tests `tests/test_calibration_v2.py`, `tests/test_coverage.py`, `tests/test_tune_v2.py`, `tests/test_promote_v2.py`, `tests/test_benchmark_v2.py`, `tests/test_lock_v2.py`.

**Interfaces — Produces:**
- `sim/calibration_v2.PROFILES`: F000 D2+H3 attack; F111 and C* x {D2+H3, X7-SC} attacks; references of F000, F111, C* (8). Q1 statistics: 2 pooled differences; `endpoints("Q1", branch)` has 8 entries; `denominator("Q1") == 8`. `select_kappa` admits the largest kappa whose every endpoint has `clopper_pearson_upper(misses, replications, 1 - 0.01 / m) <= alpha_e` on the selection replications; no fallback after a failed validation.
- `scripts/coverage_v2.SOURCE = {"F000": "B3-t", "F111": "R3-t"}`; no C*/S2 fixture inputs.
- `scripts/tune_v2`: systems B3-t, R3-t, C*-t; no fixture searches for C*/S2 (`fixture_searches` removed or reduced to none, with its CLI option refused).
- `scripts/promote_v2.SYSTEMS = ("B3-t", "R3-t", "C*-t")`; coverage promotion and `final()` no longer require `fixture_cstar_s2.json` (`final` needs comparator, coverage, the benchmark timings and decision, `decision-h4.json` when H4 is loaded, and the three tuned files); new kind `decision_h4` (Task 12 specifies the handoff): `_decision_h4(src, to, markets, code_commit)` recomputes `choose_after_h4` and writes `benchmark/decision-h4.json`.
- `scripts/benchmark_v2.choose_after_h4(timings, ledger, frozen: dict, h4_timing: dict, vcpu=16) -> dict`: keeps the frozen decision's branch and markets (the defenders are frozen); development = development spend recorded in the ledger + the remaining development work (coverage only, priced by `cost_table`), each completed item counted once; evaluation recomputed with H4 priced from `h4_timing`; the smallest cut within the evaluation cap; `stop` if none; `approval_required` on the new total.
- `scripts/benchmark_v2`: the live `counts()` derives every number from the manifest and `calibration_v2.PROFILES` (H4 cells counted as `h4`, diagnostic cells as `diagnostic`, never as plain searches; coverage profiles `len(PROFILES)`), and the pod-billing path (`_pod_table`, `eval_pods`, `default_eval_plan`) uses the three tuned systems, no fixture searches, the coalition steps of Task 5, the training matrix, and the held-out doubling evaluations. The constants are the uncut values: `CELLS = {"plain": 145, "x7": 79, "h4": 21, "welfare_h3": 6, "welfare_x7": 6, "coalition": 30}` (287); `REFERENCE_MENUS = 79` full plus `REDUCED_MENUS = 18`; `EPISODES = {"coverage": 8 * 20_000 * 3}`; `COUNTS` and `CONFIG_MARKETS` for three systems (`tuning_inner` (288, 144), `tuning_recheck` (36, 18); `fixtures_inner` 0); coalition extras: second twin (6), projection evaluations, rescoring; doubling 98 with held-out evaluations; diagnostic 3 x 200 episodes. `cost_table(timings, ..., h4_timing: dict | None = None)` prices H4 cells from `h4_timing` when given (scaled by the benchmark's pod timing of an X7-SC search), else as X7-SC cells.
- `scripts/lock_v2`: `FILES["decision_sha256"]` points to `experiments/v2/benchmark/decision-h4.json` when the protocol's `h4` is not null, else to `decision.json`; `build` refuses an H4 protocol without `decision-h4.json`.

- [ ] **Step 1: failing tests.** `test_profiles_8`, `test_q1_endpoints_8`, `test_select_kappa_uses_clopper_pearson` (a candidate whose observed miss rate is at alpha_e but whose upper bound exceeds it is not selected), `test_no_fallback_after_failed_validation`, `test_coverage_source_no_r4`, `test_tune_three_systems`, `test_promote_systems_three`, `test_promote_decision_h4_recomputes`, `test_cells_287_and_menus` (CELLS sum 287; 79 + 18 references), `test_cost_table_prices_h4_from_timing` (doubling `h4_timing["seconds"]` raises the H4 line proportionally), `test_lock_uses_decision_h4_when_h4`. `test_counts_live_match_manifest` for cuts 0 to 4 and `h4_excluded` both ways. `test_default_billing_path_draft7` (`choose()` on a synthetic timing set uses three systems, 8 coverage profiles, and prices H4 and diagnostics separately). `test_choose_after_h4_keeps_branch_and_counts_once` (with tuning spend already recorded at 7 USD and an expensive H4 timing, the branch is unchanged, tuning is not priced again, and the cut level rises before a stop). `test_final_promotion_three_systems` (`final()` succeeds without `fixture_cstar_s2.json`).
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_calibration_v2.py tests/test_coverage.py tests/test_tune_v2.py tests/test_promote_v2.py tests/test_benchmark_v2.py tests/test_lock_v2.py -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 10: eight-profile coverage with Clopper-Pearson selection, three tuned systems, draft-7 cost model, decision after H4".

## Task 11: Report constants, operations plan, H4 brief (D2, D17, design 11)

**Files:** Modify `scripts/report_v2.py` (constants), `docs/revision/h4-brief.md`, `docs/superpowers/plans/2026-10-25-revision-operations.md` (Part B), `docs/revision/predictions-v2.md` (template headings). Tests `tests/test_report_v2.py`, `tests/test_h4_check.py` (brief text assertions).

**Interfaces — Produces:**
- `scripts/report_v2`: `PAIRS = (("F111", "C*"),)`; `CORE = ("F000", "F111", "C*")`; `WHOLE = ("B3-t", "R3-t", "C*-t")`; `REPAIR` unchanged; Q3 adds X8-DB (G_tot, G_min) and the diagnostic table; fresh whole-system rows labelled "reduced menu (D2+H3)".
- `docs/revision/h4-brief.md` (design 5.3): the author may read `sim/mechanisms/`, the frozen C* and tuned files, the development simulator, instances, families and their development results, and the scoring definitions; must not read `sealed/` or another clone's `sealed2/`; the policy sees only `ProviderView` and T, L; envelope (15 knobs, finite bounds, `project`), X7-SC budget and bounded controls, at most 8 core-hours locally, CPU only, no paid API; `h4_check` prints the hash and the timing record.
- Operations plan Part B: Operation 1 (H4) moves after Operation 3 and runs at the defender-freeze commit (`h4-base` = the commit holding the promoted comparator and tuned files); a new step after Operation 1 promotes `decision_h4` (cost after H4; cuts by design 8.2 if over cap); Operation 2's smoke and Operation 3's command lines drop R4-t and the C*/S2 fixture searches; Operation 7's pod list and doubling counts follow the new manifest; the H4 custody constraint names the defender-freeze commit. Each change is listed in a "Changes in Part A2" table at the end of the operations plan.

- [ ] **Step 1: failing tests.** `test_report_constants_draft7`; `test_report_q3_has_x8_and_diagnostic`; `test_h4_brief_allows_defender_source` (the brief contains "sim/mechanisms/" in the permitted list and the envelope numbers 15 and 8 core-hours).
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement and edit the documents.
- [ ] **Step 4:** `uv run pytest tests/test_report_v2.py tests/test_h4_check.py -q`, then the whole suite `uv run pytest -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 11: report constants, H4 brief, operations plan Part B for draft 7".

## Task 12: The revised operations sequence, executable (Part B handoff)

**Files:** Modify `scripts/promote_v2.py`, `scripts/coverage_v2.py`, `scripts/h4_check.py`, `scripts/lock_v2.py`. Test `tests/test_ops_sequence_v2.py` (new; a temporary git repository with synthetic promotion inputs, smoke budgets, no pods).

**Interfaces — Produces:**
- **Defender-freeze commit:** after Operation 3's promotions, the executor commits `experiments/v2/` (comparator, tuned files, promotion record) on top of `code_commit`; that commit is `defender_commit`, tagged `h4-base` by the author. `promote_v2.same_code(repo, code_commit, commit) -> bool` is true if `code_commit` is an ancestor of `commit` and `git diff --name-only code_commit commit` touches only `lock_v2.ALLOWED` paths (`experiments/v2/`, `docs/`). Every promotion check that compares a record's commit with `code_commit` (coverage records `HEAD`, `scripts/coverage_v2.py:82`) uses `same_code`, so records made at `defender_commit` or later data-only commits are accepted and records from changed code are refused.
- **Timing units:** `h4_check.timing` measures, in the same process and on the same machine, one full-budget H4 search with its controls and one full-budget X7-SC search with its controls against F111 on the headline (dev-train seeds); the record is `{"bundle_sha256", "defender_commit", "h4_seconds", "x7_seconds", "h4_episodes", "x7_episodes", "knobs", "controls"}`. `cost_table(..., h4_timing)` prices an H4 cell as (h4_seconds / x7_seconds) x the benchmark's pod time of an X7-SC cell.
- **Handoff:** the sealed session prints the record as one JSON line; the author copies that line into `experiments/v2/h4/timing.json` (no bundle file is copied or opened). `promote_v2 --kind decision_h4 --from experiments/v2/h4` refuses a record whose `bundle_sha256` differs from the protocol's H4 hash input or whose `defender_commit` is not the promoted defenders' commit, then writes `benchmark/decision-h4.json` via `choose_after_h4`. If the new total exceeds 40 USD, `lock_v2.build` requires the approval sentence (existing rule, now on `decision-h4.json`); a `stop` ends the program for the author before coverage.

- [ ] **Step 1: failing test.** `test_ops_sequence_draft7`: in a temporary repository, `code_commit` → promote comparator and three systems → commit `defender_commit` (data only) → write a synthetic H4 timing record → `promote --kind decision_h4` → coverage records made at a later data-only commit are promoted → `final()` → `lock_v2.build` succeeds; the same sequence with a record from a commit that changes `sim/` is refused at promotion; a timing record with a wrong bundle hash is refused.
- [ ] **Step 2:** run; expected FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `uv run pytest tests/test_ops_sequence_v2.py tests/test_promote_v2.py tests/test_lock_v2.py -q`, then `uv run pytest -q`; expected PASS.
- [ ] **Step 5:** commit "A2 task 12: defender-freeze commit, H4 timing handoff, decision after H4, sequence test".

## Final review

Whole-branch review of `fee49c9..HEAD` by Sol high and Astra high (read-only), against design draft 7 and this plan's Review Focus; one fix pass with TDD for every Critical and Important finding; re-review rounds until both seats accept. The ledger is `docs/revision/part-a2-ledger-2026-10-27.md` (rulings as "Ruling: … — … — cost if wrong").

## Disposition of round 1 (both seats: reject)

| Finding | Version 2 | Task |
|---|---|---|
| Sol 1 / Astra 1: repair rules lose the fixed pair | `rules_v2.FIXED`; `rule_spec` uses it; construction test | 1 |
| Sol 2 / Astra 2: diagnostic cells block the freeze | excluded before the freeze; evaluation after it; sequence test | 1 |
| Sol 3 / Astra 3: coalition callers, reconstruction, doubling | `ProfileDescriptor`; all three callers through the factories; new tag; G_min doubling against the final reference; reload tests | 4, 5 |
| Sol 4 / Astra 4: training selections after the freeze | `bank_train`, `envelope_select`, `welfare_select` before the freeze, hashed; evaluation refuses without them | 8 |
| Sol 5 / Astra 5-6: report outputs and the Q1 sign | report integration tests; d = C* - F111 in the report | 9 |
| Sol 6 / Astra 7: nonfinite refusal misses the Q1 path | shared primitives guarded; per-test withholding; integration test | 9 |
| Sol 7: damaged current-provenance records reused | schema checks in the reuse rule for evaluate, cross, doubling | 8 |
| Sol 8 / Astra 9: billing path not tested | live counts and pod billing from the manifest; tests per cut | 10 |
| Sol 9 / Astra 10: decision after H4 double-counts and re-chooses | `choose_after_h4` keeps branch and markets, counts once | 10 |
| Sol 10 / Astra 8: `final()` requires the removed fixture | removed; `final` test | 10 |
| Sol 11 / Astra 11: operations handoff | Task 12: `same_code`, timing units with a local X7 baseline, timing handoff, decision and approval gate, sequence test | 12 |

