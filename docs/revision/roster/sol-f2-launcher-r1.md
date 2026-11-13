VERDICT: reject

CORRECTIONS:
1. `docs/revision/followup2/convergence_v2.py:274` — Preserve an inner admission refusal. If admission passes before a gate cell but fails before round 1, `run_cell` returns `"round1_gate": "not run"`. `gate_cell` converts this to `pass=false`, and line 385 returns 4. The launcher then falsely reports that round 1 differs from the registered record. Return 3 for this cost stop; return 4 only for a measured mismatch.

2. `docs/revision/followup2/test_followup2_pod_harness.sh:251` — Add a regression test for that driver path, including a STOP or deadline change between the two admission checks. The current stub returns the selected exit code directly and cannot detect the defect. I inspected the saved 29/29 log; I did not rerun the harness because it writes files.

3. `docs/revision/followup2/runner-up-plan.md:147` and `docs/revision/followup2/convergence-plan.md:156` — Apply ruling 2 to the plans: reserve the watchdog allowance, retain stop caps of 3.00/4.25 USD, and replace the exact-stop-cap grant check with sufficient-reservation validation. Update the reservation instructions at lines 166/175 and the obsolete shared category cap at lines 126/135 to 72 USD.

4. `docs/revision/followup2/launcher-notes.md:78` — After all corrections and the final commit, regenerate both Run B Mac gate records and rebuild the bundle. Both current records bind to `51b71d2`; the launcher correctly refuses them. Accept rulings 1–8 subject to these corrections. The installed launcher matches, Bash 3.2 syntax passes, and the required bundle hashes, pairing, budgets, and Run A evidence checks pass.

CONFIDENCE: 0.96.