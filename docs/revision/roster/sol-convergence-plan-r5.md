VERDICT: reject

CORRECTIONS:

1. **§§5,7; round-4 correction 2 remains open.** Both saved Mac gate records report zero difference, but their bindings identify an older driver, guards, plan, and commit. Saved/current driver hashes start `8b0b2383`/`22d533f5`; guards `e7d91d58`/`1682ec1c`; plan `30d2db09`/`b7ea0c1a`. The inventory’s current hashes do not repair these bindings. Complete both gates from one frozen code snapshot and validate the complete bindings before pod creation. This is an evidence mismatch, not a numerical gate failure. Both Run A evidence directories validate.

2. **§6; round-4 correction 1 remains partly open.** The parser now accepts the launcher’s event format, and the driver checks STOP and the soft deadline. However, the inspected launcher still lacks the specified file transfers and billing arguments; no Run B launcher copy was present. Prepare that copy and test the complete handoff offline, including a failed attempt and earlier ledger spend, before pod creation.

3. **§6, lines 137–146.** Remove the obsolete four-field attempts format and nonexistent `guards.prior_from_attempts` reference. Use the three-field events and `guards.attempts_spend` consistently. Replace the Run B `--stage all` statement with its actual gate and round checks.

4. **none — §§1–5; remaining round-4 corrections.** All 19 jobs pass pairing, configuration, budget, and code checks; all 111 dependency hashes match. Report entries match registered doubling records. Result bindings, minimum-round passes, and exclusion of cost-stopped partial results remain correct. The design addresses bounded search sensitivity; it does not establish convergence. Expectations timing, nominal conditional intervals, and deferrals are appropriate. Forty tests requiring no file writes pass; the full suite was not run.

5. **none — §6.** Benchmark arithmetic reproduces 29.48 core-hours, USD 3.30 estimated cost, and USD 4.12 with allowance, below the USD 4.25 admission cap. Preserve the stated watchdog exception and reserve the allocation before launch.

CONFIDENCE: 0.98