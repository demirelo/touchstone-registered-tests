VERDICT: reject

CORRECTIONS:

1. **Plan §3 — none for the tolerance deviation.** Both saved reproductions pass the current comparator: maximum knob drift is 2.58e-13 relative; gain drift is 2.02e-14 absolute. The 1e-9 limits are reasonable for this reproduction. Draft 5 explicitly records the deviation, acknowledges the Mac corner discrepancy, and requires a pod gate. It correctly leaves the drift source unresolved.

2. **`docs/revision/followup/reset_followup_v2.py:383` — correct `identical`.** In-memory checks returned `identical: true` after changing the twin value by 5e-10 or one control value by 1.0. Require exact numerical equality for that label, or rename it `selected_knobs_and_gains_identical`. The tolerance-based pass result otherwise implements the stated criterion.

3. **Plan §§3(d), 8 — block pod creation until current validation evidence exists.** The old doubling record passes the current numerical comparator but lacks provenance, dependency hashes, and inventory. `followup-repro-doubling-v2` still lacks its doubling record, gate, and inventory. The supplied headline reproductions also lack saved gates and inventories from the corrected path. Complete and save the required validations before provisioning.

4. **Plan §§4, 8; `docs/revision/followup/reset_followup_v2.py:130`; `docs/revision/followup/test_reset_followup.py:304` — complete headline diagnostic coverage.** The CLI builds only fresh-market jobs; the headline test covers only F111 at smoke size. Specify an executable path that saves all three headline rules on 200 evaluation seeds. Combined with the fresh-market diagnostics, it must cover the promised 63 policies and 42 switch comparisons.

5. **Plan §§3–6 — none for the remaining round-4 corrections.** Pairing, code, salt, output protection, input conflicts, freeze membership, source-based acceptance, and environment fields address findings 1, 2, 5–8. Reverse-switch construction, per-seed outputs, zero-reset enforcement, separate five-market denominator gates, all-six scoring, and explicit best-of deferral are clear. I inspected the tests but did not rerun the writing test suite under read-only access.

CONFIDENCE: 0.96.