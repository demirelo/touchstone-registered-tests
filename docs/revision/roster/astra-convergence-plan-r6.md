VERDICT: reject

CORRECTIONS:

1. **§6; guards.py:155–176.** Reject malformed ledger data before admission. `ledger_spend()` treats a missing `spent` field as zero and accepts negative amounts. In-memory checks confirmed that `guards.py admit` returns 0 for `{}` and for a matching −4 USD spend row; the latter produces negative prior spend. Require the ledger structure and finite, nonnegative amounts. Add refusal tests.

2. **§6, “Admission before every paid step”; convergence-plan.md:150–151.** Use `budget_followup.py --reserve convergence-<n> 3.40`. The CLI requires `--reserve`. Also require the returned grant to equal 4.25 USD before allocation: `budget_v2.reserve()` can grant less when category capacity is limited. An in-memory check returned 4.00 USD for a 3.40 USD estimate. Multiplication by 1.25 alone does not guarantee the reservation.

3. **§§5,7.** Complete and validate both Mac gates against the final frozen snapshot before allocation. At inspection, both files under `followup2-conv-gate/gate/` reported passes but retained older guards and plan hashes. Current bindings reject them. This is pending evidence, not a numerical failure. Run A’s reproduction and doubling evidence both validate, including recomputed comparisons.

4. **none — remaining round-5 corrections, §6.** Attempt validation now rejects unordered or nonfinite epochs, multiple open attempts, and inconsistent allocation times. Prior attempts and matching ledger spend enter admission; STOP and deadline checks remain present. Obsolete format references are removed. Keep the launcher copy and its offline handoff test as the named allocation prerequisite; their absence is not a defect within this review’s implementation scope.

5. **none — §§1–5 and cost arithmetic.** The design measures bounded search sensitivity and addresses part of the review’s concern. Expectations timing, nominal conditional intervals, deferrals, and preservation of registered decisions are appropriate. All 19 jobs and 111 dependency hashes validate; report doubling entries match registered records. Earlier binding, pass-status, and partial-result corrections remain intact. The benchmark reproduces USD 3.30, or USD 4.12 with allowance, below the USD 4.25 admission cap. Forty-one read-only tests pass; 41 write-dependent tests were excluded.

CONFIDENCE: 0.97