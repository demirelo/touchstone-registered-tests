# Reset follow-up: analysis code and paper change, internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

The reset pod ran (gate bit-identical; 18 D2 cells; records in `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-reset-pod/`, inventory verified, 228 records 0 bad). Mac diagnostics with the pod's code: `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-reset-mac-diag/` (`spot_compare.json`: the spot cell matches the pod, counts exact, max abs diff 2.2e-16).

Spec: `docs/revision/reset-experiment-plan.md` sections 1, 2, 4, 5, 6, 8 (steps 5 and 6). Commits to review: 3e286c1, 41bafd2, 05d1240, 0f62b18 (`git show`).

Files:
- `docs/revision/posthoc/reset_block.py` and `test_reset_block.py` (20 tests): loading, paired bootstrap, gated S, leave-one-out, sign counts, expectation scoring, switch summary, headline values, table, CLI.
- `docs/revision/posthoc/reset.json` (output) and `docs/revision/paper-v2/tables/posthoc_reset.tex`.
- `docs/revision/paper-v2/main.tex`: the paragraph "Identity replacement and the B3--R3 gap (exploratory follow-up)" and `tab:ph-reset`; `sites.json` (29 new `rs_*` sites); `numbers_v2.py` (new kind `share_s`) and `test_numbers.py`.

Rulings to accept or reject:
1. A separate module with its own command line, not new code inside `posthoc_v2.py` (plan step 6 says "a new reset block in posthoc_v2.py"); posthoc.json and its tables are untouched.
2. Bootstrap seed 20261109 (the plan fixes no seed).
3. The paper sentence "Within the D2 family, at the fixed parameters and search budgets, most of the estimated B3 minus R3 gap under the prescribed searches disappears when the attacker cannot replace its identity" is used because the pooled-S expectation scored "met" (plan section 6).

Check:
(1) Each statistic of plan section 5 and each scoring rule of section 6 is implemented as written (pairing: one index vector per market for every rule and family; pooled = mean of six market means; gate on the lower bound of pooled G(D2+H3) > 0.05, also per leave-one-out; base and doubled separately; met / failed / not established; missing or undefined reported separately).
(2) The loaded records are the right ones (D2+H3 from `results/v2/eval/all`, D2 from the pod, doubled D2+H3 from `report.json` doubling heldout, doubled D2 from the pod's doubling records) and the seeds checks are sound.
(3) Every number in the paragraph and table matches `reset.json`, and the prose claims nothing the plan forbids (it is a descriptive follow-up specified after the headline contrast was seen; no confirmatory claim; I is a difference of two prescribed searches).
(4) Defects the tests miss.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
