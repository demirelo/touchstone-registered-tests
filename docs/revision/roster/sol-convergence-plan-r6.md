VERDICT: reject

CORRECTIONS:

1. **§6; `guards.py:101`, `guards.py:155`, `guards.py:170`, `guards.py:310`.** Validate admission amounts before comparison. An in-memory CLI check returned exit 0 with USD 5.56 already spent against a USD 4.25 cap when `--hours -10` was supplied. Negative ledger spend also reduced prior cost; an infinite cap permitted admission. Require finite positive cap/rate, finite nonnegative step estimates and ledger amounts, and a valid ledger structure. Add refusal tests.

2. **§6, “Admission before every paid step”; `convergence-plan.md:150`.** Correct the reservation command to `python3 docs/revision/followup/budget_followup.py --reserve convergence-<n> 3.40`. The CLI requires `--reserve`, not `reserve`. Check that the returned grant equals USD 4.25; available ledger capacity can reduce it.

3. **§§5,7 — pending evidence.** Both files currently in Run B’s `gate/` report zero numerical difference, but their bindings still contain draft-5 guards and plan hashes (`1682ec1c…`, `b7ea0c1a…`), rather than current hashes (`ab470ea6…`, `126113fe…`). Complete and validate the stated rerun against the frozen launch snapshot before allocation. This is pending evidence, not a numerical gate failure. Both Run A evidence directories validate, including recomputed comparisons.

4. **none — remaining round-5 corrections; §§5–6.** Attempt ordering, finite epochs, exactly one open attempt, and allocation-time checks pass in-memory checks. Earlier attempts and ledger spend count correctly for valid inputs. STOP/deadline checks remain present. The separate launcher copy and its offline handoff test are correctly named prerequisites; their absence does not itself require a driver correction.

5. **none — §§1–4,6.** All 19 jobs pass pairing, configuration, budget, and code checks; all 111 input hashes match. Report entries match registered doubling records. Labels, references, banks, bindings, partial-result exclusion, and output separation remain consistent. The design measures bounded search sensitivity, with suitable expectations timing, nominal conditional intervals, and explicit deferrals. Cost reproduces USD 3.30, or USD 4.12 with allowance, below the USD 4.25 admission cap. Forty-one read-only tests pass; 41 write-dependent tests were excluded.

CONFIDENCE: 0.97