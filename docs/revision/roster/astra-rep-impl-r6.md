VERDICT: reject

CORRECTIONS:

1. **K1 — `docs/revision/followup3/rep_collect.py:287`, `_mismatch`:** Validate the comparison before classifying a mismatch. In-memory probes with `round1_gate={}` or `max_gain_abs=NaN` produced `round1_mismatch=True`, removed the primary set, and stopped resume with exit 4 without rerunning. These malformed records must follow the invalid-record path.

2. **K1 — `docs/revision/followup3/rep_collect.py:546`, `:563`, `:581`:** Check measured disagreements before skipping unscorable cells. Changing round-1 `attack_change` to `0.02` and removing that cell’s evaluation produced `round1_mismatch=False`; another cell’s continued winner remained in the primary set. Invalid evaluation seeds produced the same failure. The initial scan lacks the doubling/search inputs needed to detect this disagreement.

3. **K3 — `docs/revision/followup3/rep_collect.py:104`, `flagged_cells`:** Apply the non-object-root check during queue construction. A doubling record containing `[]` raises `AttributeError` at `.get("incomplete")`. It must count as absent.

4. **K3 — `docs/revision/followup3/rep_collect.py:434`, `base_problem`:** Validate the doubling record’s computed normalizers. Setting its held-out `sstar` to `[5e-324, 4.0]` with `N=4` leaves the cell scorable and its continued winner selected, although the first normalizer becomes zero. The evaluation and continuation checks do not cover this doubling-record failure.

5. **K4/K5 — `docs/revision/followup3/test_rep_collect.py:939`; `rep-launcher-notes.md`, ruling 10; `rep-impl-r5-response.md`, K1–K5:** Require distinct outcomes for malformed records and measured mismatches. The guard currently accepts either loss of the primary set or refusal of a continued winner, so it passes the incorrect permanent stop in correction 1. Add queue-construction, resume, invalid-base, and doubling-normalizer cases; correct the completion claims. The probes above ran in memory. The full suite could not run because the sandbox blocked cache and temporary-file creation.

CONFIDENCE: 0.99.