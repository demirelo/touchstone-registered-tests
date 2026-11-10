VERDICT: reject

CORRECTIONS:
1. **None — plan §3, tolerance deviation.** Both saved search runs pass the current comparator: maximum knob drift is 2.58e-13 relative; gain drift is 2.02e-14 absolute. The 1e-9 limits are justified for this reproduction, and the plan explicitly records the deviation. The revised wording correctly avoids claiming that bit identity is impossible.

2. **`docs/revision/followup/reset_followup_v2.py:326` — finish round-4 comparator correction.** Explicitly retain or reject exact twin and corner-control values. They remain unchecked. An in-memory change of the twin best value to 123 passes and reports `identical`; a NaN attack best value does too. Define the scope of “every value finite” and enforce it.

3. **`docs/revision/followup/reset_followup_v2.py:365,389,433` — block the pod.** Doubling reproduction bypasses preflight checks and saves neither a comparison result nor an inventory. Its comparator accepts NaN gains and NaN attack changes. Add finite-value checks, apply preflight, and save the result and environment. The specified `followup-repro-doubling` directory currently lacks the doubling output; no passing ground truth is available there.

4. **`docs/revision/followup/reset_followup_v2.py:169` — complete input validation.** `fr["records"].get(u, s)` accepts a copied search absent from the original freeze. An in-memory check confirms this. Require membership for copied searches as well as matching hashes. Explicit cuts fields and conflicting-hash rejection are corrected.

5. **Plan §§4,8; `reset_followup_v2.py:445` — align execution instructions.** Diagnostics and reverse switches now exist, but default `all` runs diagnostics on the pod. Specify the pod stage sequence, Mac diagnostics after retrieval, headline coverage, and the required passing doubling result before provisioning. Section 8 still lists only validations (a) and (b).

6. **None — remaining driver checks.** Main-path pairing, code, salt, output protection, source-based acceptance, and environment fields address the cited findings. Headline reproduction now runs preflight and saves gate evidence; existing reproduction directories predate those additions.

7. **None — plan §§5–6.** Separate five-market denominator gates, base/doubled reporting, all-six scoring, and explicit best-of deferral close those round-4 corrections.

CONFIDENCE: 0.97