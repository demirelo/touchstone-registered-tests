VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup3/rep_collect.py:299` — K1 still classifies malformed comparisons as mismatches. Setting `round1_gate.max_gain_abs=None` causes resume to exit 4 without rerunning and removes the primary set in analysis. Validate the comparison before testing identity. A malformed comparison must follow the invalid-record rule.

2. `docs/revision/followup3/rep_collect.py:546`, `:562`, `:578` — K1’s global stop remains incomplete. With a well-formed round-1 `attack_change=0.02` against doubling’s `0.01`, removing that cell’s evaluation record makes collection skip its comparison. The probe returned `round1_mismatch=False` and retained another market’s primary results, although `_mismatch` with the cell’s dependencies returned True. Check round-1 disagreements before base-record exclusions.

3. `docs/revision/followup3/rep_collect.py:104` — K3 misses queue construction. A doubling record with JSON root `[]` still raises `AttributeError` in `flagged_cells`, which `stage_continue` calls before `run_queue`. Apply the object-root check here and treat other roots as absent.

4. `docs/revision/followup3/rep_collect.py:269`, `:361`, `:386`, `:507` — K3’s computed-normalizer check runs only during scoring. A saved gate with `sstar=[5e-324,4.0]`, N=4, passes collection and resume; resume exits 0. A continuation with that normalizer is also reused without rerunning. Apply computed-normalizer and finite-term checks in the shared validation used by gates and resume.

5. `docs/revision/followup3/test_rep_collect.py:914`; `rep-impl-r5-response.md:K1–K5`; `rep-launcher-notes.md`, ruling 10 — K2’s cross-checks and K4’s seven-kind enumeration are present. However, the guard permits a malformed continuation to remove the primary set and tests collection without queue construction or resume. Add exact outcome checks for the failures above and correct the completion claims. All 164 existing tests passed; the cited harness log’s hashes match the current launcher and harness.

CONFIDENCE: 0.99.