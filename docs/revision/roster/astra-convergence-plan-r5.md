VERDICT: reject

CORRECTIONS:

1. **§6; `guards.py:115–163`.** Complete attempt validation. The parser accepts multiple open attempts and globally unordered timestamps; `paid_cost_stop()` discards the open-attempt list. An in-memory check accepted two open pods, counted zero prior spend, and admitted another round. A future `--started-at` also produced negative spend. Require ordered, finite timestamps, exactly one current open attempt, and a consistent allocation time no later than now. Add refusal tests.

2. **§6; `results/pods/reset_pod.sh:112–136`.** Complete the launcher copy and test its handoff without creating a pod. Event-format compatibility is corrected, and STOP/deadline checks exist, but the supplied template does not transfer the attempts file or ledger or pass the new billing arguments. Test a failed attempt, a previous launch, file transfer, and both paid commands. Remove the obsolete four-field format and nonexistent `guards.prior_from_attempts` reference at `convergence-plan.md:146`.

3. **§§5,7.** Keep pod creation blocked until both draft-5 Mac gates validate against the frozen launch commit. At inspection, both files in `followup2-conv-gate/gate/` passed with zero difference but retained older driver, guard, plan, and commit bindings. The stated rerun remains pending evidence, not a failed experiment. Run A’s reproduction and doubling records, inventories, and recomputed comparisons validate. Require matching pod evidence before continuation.

4. **none — §§1–5.** The estimand measures bounded search sensitivity and addresses part of the review’s concern. It does not establish convergence or resolve deferred coalition and factorial searches. Expectations precede new continuation outcomes; nominal conditional intervals and unchanged registered decisions are appropriate. All 19 jobs pass pairing, configuration, budget, and code checks; all 111 input hashes match. Report entries match registered doubling records. Earlier binding, pass-status, and partial-result corrections remain intact.

5. **none — §6.** Benchmark arithmetic reproduces 29.48 core-hours, USD 3.30 estimated cost, and USD 4.12 with allowance, below the USD 4.25 admission cap. Forty read-only tests pass; 38 write-dependent tests were excluded. The cap remains an admission limit, with the stated watchdog exception.

CONFIDENCE: 0.98