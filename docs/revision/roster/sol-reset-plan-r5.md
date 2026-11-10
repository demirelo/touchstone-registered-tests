VERDICT: reject

CORRECTIONS:

1. **§3; `reset_followup_v2.py:326`:** The tolerance change is justified for the selected knobs and gains and is explicitly recorded. Both saved reproductions pass. However, round 4 requested an explicit decision on twin values and corner controls. These remain unchecked. Mac corner control 44 differs from the registered value by **1.52e-5**, despite identical knobs. Investigate this difference and record the comparison requirements. The evidence does not isolate drift to optimizer arithmetic.

2. **`reset_followup_v2.py:365`:** Block the pod until `compare_doubling()` rejects nonfinite values. In-memory checks accepted NaN gains, continuous knobs, attack change, and reference change. Require the compared fields instead of supplying defaults. Also resolve §3’s blanket “Every value finite”: `compare()` accepts NaN attack, twin, and control objective values.

3. **§3(d); `reset_followup_v2.py:389`:** Apply salt, commit, code, pairing, and configuration checks before doubling reproduction. This path bypasses them and writes a record without provenance or dependency hashes. Save the comparison result and environment inventory. No completed doubling record exists in `followup-repro-doubling`; a valid saved pass remains required before pod creation.

4. **§4; `reset_followup_v2.py:299`:** Complete the pod/Mac diagnostic comparison contract. Save seed identifiers and per-seed normalized profits and switch differences; specify exact checks for reset/ban counts and tolerances for numerical results. The current output retains profit and switch means only. Enforce the zero-reset check for every D2 winner.

5. **§§3, 5–6: none** for the corrected headline reproduction checks, input conflicts and freeze assertions, source-path protection, acceptance recomputation, and environment fields. Reverse-switch construction, five-market denominator gates, base/doubled reporting, all-six scoring, and the explicit nested-best-of deferral are clear.

CONFIDENCE: 0.97.