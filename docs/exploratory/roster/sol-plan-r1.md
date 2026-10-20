VERDICT: reject. The plan has material correctness failures: X4 and X6 do not reproduce HonestMax at their honest points. X6 can also select a unilateral reference with cached coalition scores. The repairs below are checkable without changes to frozen files.

REPAIRS:

1. **Task 1, identity clock:** record the replacement round when the policy emits `exit=True`. Select that round’s action with effective age zero. On the next call, associate the new identity with the recorded replacement round. `market.py` requests actions before it creates replacement identities; detecting the changed identity alone starts the clock one round late. Add episode tests for replacement-round effort, first-offer age, ban return, and consecutive replacements.

2. **Task 2, X1:** use knobs `u,m,s,w,theta,lhat,x,clip` (8), with theta in [0,1], lhat in [1,30], and binary x. Fix kappa at 1. This removes the existing `0/0` when kappa=0 and a bucket is empty. Let x enable replacement after failure. Assign each historical observation to the bucket of its action round. Add a public pacing feature or state that this tests learned audit exposure only. A fitted audit threshold does not directly test the stated expected-sanction condition.

3. **Task 2, X2 and X3:** for X2, use separate EWMAs for fresh, established, and terminal phases, with public L=10 and unchanged knobs. State that neither job-specific effort nor actual tranche identification is tested. For X3, retain its eight knobs and optional z. Add exact diagnostic candidates for windows `[10,190)` and `[190,200)`, with z=0, and report their additional run counts. Do not force terminal cheating: R3 reserves audits there. Label remaining-stock inference as untested; realized stock is unavailable.

4. **Task 2, X4:** add binary x, giving `u,m,s,w,lambda,lhat,x,clip` (8). Exit only when x=1 and the inequality holds. Its honest point then has x=0. Delete “no failed audits”: honest delivery can fail because of noise. Define the observed profit proxy as `payment-refunded-served*(a+b*previous_effort)`. Save previous effort and eligibility before enforcement. Include failed service rounds in estimates. Define initialization and no-service updates. Cap remaining banned rounds at `min(B,T)-t`. Call these learned value proxies, not identified counterfactual continuation values.

5. **Task 2, X6:** change P to [0,50], with `round(P)=0` disabling scheduled resets and positive integers giving the period. Keep `u,m,s,w,P,x,clip` (7). The present honest point has P=2 and therefore exits repeatedly. Add a forced noisy-failure HonestMax fixture for every family. Test complete episode trajectories and twin containment, beyond action equality on scripted histories.

6. **Task 3, coalition reference:** rescore admissible reference candidates with honest opponents before ranking archive candidates or selecting the reference. Remove coalition `known_profit` and `known_normalized`; `select_reference` otherwise trusts these arrays. Test a fixture where coalition and unilateral rankings reverse. Construct both searches through the coalition objective, clip every member in twin runs, and verify all-member projection equivalence. Label the objective “focal profit under a coordinated profile”; it does not maximize coalition profit.

7. **Tasks 3–4, coalition accounting:** specify each member’s reference procedure for mean member profit change. Distinguish focal harm, which includes coalition partners among “others,” from harm to outsiders. Do not call partners’ bans false bans. Add matched c=1 and staggered-entry controls with the same reset count. Report actual fresh served jobs, priority audits, and uncovered fresh jobs. Capacity depends on service demand exceeding quota, not c alone.

8. **Task 3, bank and resume:** define immutable bank membership, canonical ordering, exact-key deduplication, X6 size compatibility, and tie handling. Include projected members in reference selection. Differential-test the local bank against frozen `Bank` on registered synthetic fixtures; include corner replacement, projection replacement, and ties. Hash the runner as well as policies, configuration, seeds, salt identity, bank members, and source records. Write completed stage records atomically. Reject smoke records in production. Explicitly allowlist dev-train/dev-val seeds: locked `final_eval` is null, so the proposed disjointness test is insufficient.

9. **Tasks 0, 4–5:** commit predictions before any experimental run, including smoke runs, and disclose prior dev-val use. Report both gain terms, the efficiency quadruple, net efficiency, bans, and focal identity counts; `n_identities_attack` counts all market identities. Place matched D2+H3 dev-val controls beside exploratory rows. Separately label the published 40-seed final results. Add restart diagnostics and selected budget-doubling checks. Replace the unverified pod estimate with a measured full-stage benchmark and an episode-count manifest. Add cleanup on failure or interruption.

ANSWERS:

1. X5 matches the stated aging test most directly. X4 tests a continuation-value heuristic after repair. X6 requires controlled entry comparisons to establish quota pressure. X1 omits the economic sanction calculation. X2 and X3 are restricted proxies because the interface hides job-level action choices, tranche membership, other entrants, and realized audit stock. State these limits beside each result.

2. X1 should include replacement; repair 2 provides an eight-dimensional set. Keep X4 and X5 separate so their effects remain identifiable. X4’s added x permits selective reset or no reset. X3 already permits terminal cheating through z and its window; forcing it would restrict the search. Exact schedule-aligned controls address a more useful search gap.

3. The main failures are noisy honest-point behavior, replacement timing, gross funding treated as profit, and cached coalition reference scores. Add tests for repeated calls in one round, history updates exactly once, separate policy instances, and behavior unchanged by identity relabeling. Information access must remain limited to ProviderView and declared public constants.

4. The stated cells and descriptive n=20 bounds fit section 4. They establish neither coverage nor robustness at other positions. Keep every row, negative gains, and degenerate-bound flags. Matched registered-family controls are more urgent than another position. A second position is useful as a separately declared sensitivity test, without selecting it from dev-val outcomes.

5. The new-file architecture is sound. No frozen file must change if the interface limits are accepted. The coalition objective, reference rescoring, and local bank need explicit tests. The plan already counts 256 corner points within 16,300 search episodes for an eight-dimensional cell; corners are not 256 extra episodes. Pod time and cost remain unverified until measured.

CONFIDENCE: 0.95.
