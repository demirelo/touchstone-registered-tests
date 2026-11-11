VERDICT: reject

CORRECTIONS:

1. **Block pod — §5; `docs/revision/followup2/guards.py:150`.** Admission permits a later `--started-at` that omits current-pod billing. An in-memory probe supplied USD 2.50 prior spend, an open attempt lasting one hour, and allocation time equal to now. Admission allowed the USD 0.3416 reproduction gate although accumulated spend was already USD 3.06. Count from the recorded open event or enforce a verified allocation timestamp. Add a refusal test.

2. **Block pod — §5; `docs/revision/followup2/guards.py:160`.** `ledger_spend()` accepts `{}` as zero prior spend; paid admission then succeeds. Require the ledger’s expected structure and finite, nonnegative spending values. Missing accounting fields must cause refusal. Add refusal tests.

3. **§2; `docs/revision/followup2/guards.py:213`.** The round-5 supporting-record correction remains incomplete: search-stage validation is absent. An in-memory mutation changed the real reproduction search’s stage, updated dependent hashes and the inventory, and still passed the real comparison and evidence guard. Require the expected search stage and cell identity. Add this refusal test.

4. **§5; `docs/revision/followup2/runner-up-plan.md:140`.** Correct the reservation command to `python3 docs/revision/followup/budget_followup.py --reserve runner-up-<n> 2.40`. Verify that its returned grant is USD 3.00 before allocation. The wrapper can grant less when category headroom is insufficient; multiplication by 1.25 alone does not guarantee the grant.

5. **None — §§1, 3–4 and remaining round-5 corrections.** The estimand answers sensitivity to this selected alternative. Expectations, matched base/doubled contrasts, nominal interval limits, and deferrals are appropriate. All 12 job checks and 108 bank hashes passed. Both Run A gates passed current-code recomputation. Cost reproduced: 17.65 core-hours and USD 1.99 billed estimate. Attempts ordering, supporting evaluation/doubling checks, and STOP/deadline checks are present.

6. **Before allocation — §§2, 5–6.** Keep the launcher copy and offline test as the separate named prerequisite. Forty-one tests requiring no file writes passed; the other 41, including smoke execution, were not run. Run B’s current gate files still differed from this worktree’s `guards.py` and plan hashes at inspection; its rerun remains pending, independently of Run A.

CONFIDENCE: 0.98