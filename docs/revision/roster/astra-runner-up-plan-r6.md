VERDICT: reject

CORRECTIONS:

1. **Block pod — §5; `docs/revision/followup2/guards.py:148`, `:176`.** Bind accounting to the current attempt’s recorded start. The guard accepts any `--started-at` between that event and now, then discards `open_start`. An in-memory probe with five elapsed hours accepted `started-at=now`, reducing counted spend from USD 2.80 to zero and admitting the USD 0.342 reproduction gate. Derive the accounting start from the event, or require a consistent, conservative allocation timestamp. Add a refusal test.

2. **§2; `docs/revision/followup2/guards.py:213`.** Complete supporting-record identity checks. An in-memory modification of real reproduction evidence passed with an unrelated search stage and wrong search/provenance IDs after dependent hashes were updated. The real numerical comparison still passed. Require `stage="search"` and the expected cell ID in the record and provenance; require the evaluation’s corresponding identity. Add refusal tests without replacing the comparison functions.

3. **§5, “Admission before every paid step”; `docs/revision/followup/budget_followup.py:53`.** Correct the reservation command to `python3 docs/revision/followup/budget_followup.py --reserve runner-up-<n> 2.40`. The stated command without `--reserve` exits with an argument error. Require verification that the returned grant equals USD 3.00; the budget function can return a smaller grant when category headroom is limited.

4. **§§2, 5–6 — prerequisites.** Keep the launcher copy and its offline test as the named allocation prerequisite; their absence is not an additional driver rejection. Require cumulative admission before reproduction, argument transfer, STOP/deadline handling, retrieval, and verified deletion. Forty-one read-only tests passed; the full 82-test suite and smoke run were not rerun.

5. **None — remaining round-5 checks and §§1–4.** Both Run A Mac gates pass current validation and recomputed comparisons. All 12 job checks, 108 bank hashes, and registered base/doubled seed pairings passed. The bounded estimand, advance expectation, nominal interval limits, and deferrals are appropriate. Cost reproduces: 17.65 core-hours and USD 1.99 billed estimate.

6. **Run B evidence.** At inspection, both `gate/` records reported passes, but their `guards.py` and plan hashes differed from this checkout. Require matching final-code evidence before Run B.

CONFIDENCE: 0.98