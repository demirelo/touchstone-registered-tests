VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup2/followup2_pod.sh:66` — Require reservation `op == "followup"` and identify the reservation assigned to this launch. The current check accepts any matching tag prefix. A read-only reproduction accepted a `development` reservation for Run A.

2. `docs/revision/followup2/followup2_pod.sh:129` — Protect accounting across launch tags. Different TAG values take different locks but can use the same reservation and ledger PRIOR. Also, line 241 uploads the ledger again after line 47 calculated deadlines. A ledger change can therefore give the driver different accounting inputs. Hold a run-level lock, require earlier spend reconciliation, and use one validated ledger snapshot for deadlines and admission. Rulings 3–4 need these conditions.

3. `docs/revision/followup2/convergence_v2.py:273` — Preserve an inner admission refusal as exit 3. If STOP, time, or remaining budget changes after the outer check, `run_cell` can return `"stopped at the cost cap"` with `"round1_gate": "not run"`. `gate_cell` converts this to `pass: false`; line 385 then returns 4, and the launcher falsely reports a numerical gate failure.

4. `docs/revision/followup2/runner-up-plan.md:147` and `docs/revision/followup2/convergence-plan.md:156` — Accept ruling 2’s watchdog reservation, but amend both plans and their execution steps: reservation inputs 3.12/4.42, grants 3.90/5.525, unchanged stop caps 3.00/4.25, and category cap 72. Replace the contradictory stop-cap grant requirement. Accept rulings 1 and 5–8; Run B’s stale evidence must still be regenerated.

5. `docs/revision/followup2/test_followup2_pod_harness.sh:199` — Add wrong-category reservation, shared-reservation/concurrent-tag, ledger-change, and real inner-gate admission tests. The stub directly supplies exit 3 and misses correction 3. The saved 29/29 log was verified; file-writing suites were not rerun. Bash 3.2 syntax and installed-copy equality passed. Required bundle hashes, Run A evidence, and inputs for 12/19 jobs passed read-only checks.

CONFIDENCE: 0.95.