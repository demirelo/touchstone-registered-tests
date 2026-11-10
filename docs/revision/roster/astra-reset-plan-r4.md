VERDICT: reject

CORRECTIONS:

1. **§3, plan:90–101:** The tolerance change is justified and explicitly recorded. I verified maximum knob drift of 2.57e-13 relative and gain drift of 2.02e-14 absolute. Replace “bit identity … is not attainable” with “these runs did not reproduce bit identity”; the evidence does not establish impossibility.

2. **`reset_followup_v2.py:239–266` — block the pod:** `compare()` does not implement the full criterion. Check runner, salt, rule parameters, root, training/validation seeds, twin archive size, and evaluation dependencies/reference hashes. Reject nonfinite values. In-memory checks showed that changed provenance, an empty twin archive, removed evaluation dependencies, and NaN gains all pass. Define which hashes must match; new search/freeze hashes will differ.

3. **`reset_followup_v2.py:269–304` — block the pod:** `--reproduce` bypasses code, commit, pairing, and early salt checks, then returns without an inventory. Apply these checks before reproduction search and save its environment and result. Include BLAS and optimizer versions. The Linux evidence still records `git_commit: unknown`. The normal execution path addresses findings 1, 5, 6, and 8; finding 2 remains incomplete.

4. **`reset_followup_v2.py:120–140`:** Finding 7 remains partly open. Require explicit `cuts` and `h4_excluded` fields instead of accepting missing fields through defaults. Check copied search hashes against their original freeze as well as upstream records.

5. **§4, plan:110–118 — block the pod:** Diagnostics remain unimplemented. Build and test them before spend. Run existing-policy diagnostics before the pod; run fresh D2 diagnostics and reverse switches after those winners exist. Specify D2+H3 construction for `x=1`, the reverse-switch contrast, reset/ban counting, and the fixed spot-check cell.

6. **§3:104–105; §8:193:** Select the doubling ground-truth record now. Define comparisons for held-out knobs/gains, attack change, reference change, and flags; `compare()` cannot validate doubling records. Require a saved passing result before pod creation.

7. **§5:132–137; §6:146–151:** All-six scoring is clear. Specify separate five-market denominator gates for leave-one-out S, undefined-value handling, and base/doubled reporting.

CONFIDENCE: 0.97.