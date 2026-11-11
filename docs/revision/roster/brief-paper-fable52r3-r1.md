# Paper changes after Fable 5.2 external review r3: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

The external review is `docs/revision/roster/fable52-paper-r3.md` (WEIS 2/5 upper end). It found the reset follow-up reproducible and asked for fixes on existing records (its section 5, problems 1 to 7; problem 8, length, is the separate venue cut). Commits to review: 37ace39 (reset block market-level checks, tests first) and bd2dadf (paper text, number sites, kinds, ledger entry, and the reference check in `docs/revision/posthoc/reset_reference/`). Use `git show`. Data: `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all/`, `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-reset-pod/`, `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-reset-mac-diag/diagnostics.json`. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf_fable3/main.pdf` (33 pages). The paper gate passes.

Rulings to accept or reject:
1. Problem 2 (the truthful reference may replace): checked by running the 18 frozen references on the Mac with reset counting (`ref_resets.py`), and again with replacement disabled (X7-SC: h_R = T and lambda = 1; D2+H3: x = 0). The Mac does not reproduce the Linux reference profits seed for seed (largest mean difference 0.007, on fresh4 B3, which is also the largest replacement value, 0.009). The paper reports the pooled shift (0.0005) and S (1.050) with that caveat. No re-evaluation on Linux.
2. The leave-one-out range and the Mac check numbers use new number kinds (`share_s` leaves "0", "1", "S_with_non_replacing_references"; gain leaves "max_change", "G_shift_pooled", "max_abs_replacement_value", "max_abs_validation_mean_diff"; count leaf "refs_with_any_reset").
3. The abstract and conclusion each get one sentence labelled exploratory. The conclusion says that without replacement neither gap "is distinguishable from zero across the six markets".

Check:
(1) Each new number against the data. Recompute the G(D2) and C* minus R3 market t intervals and sign counts, the leave-one-out range, the flags (3 of 18, 0.044), the nesting values, the fresh0 G(D2) frozen and doubled values, and the reference summary from `reset_reference.json`.
(2) Whether each Fable r3 problem 1 to 7 is resolved, and whether `ref_resets.py` measures what the paper says. Is the no-replacement mapping right (see `sim/policies/x7.py` and `sim/policies/identity.py`)? Does a reference shift move G(D2+H3) and G(D2) equally?
(3) Overclaims or errors in the changed lines, in particular the abstract sentence ("R3's measured advantage lies in the replacement channel"), the S reading, and the reference sentence.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with a main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
