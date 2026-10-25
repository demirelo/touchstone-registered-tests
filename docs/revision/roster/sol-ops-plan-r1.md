VERDICT: reject

FINDINGS:

1. **Critical — Task 2:70; Task 3:87; `scripts/coverage_v2.py:86–91`.** Failed validation leaves the selected `kappa` numeric and sets `admitted=False`. The plan requires a validation block, but does not require admission. A failed procedure can therefore receive confirmatory decisions. **Repair:** write protocol kappa as null unless validation admits it; check replication counts, endpoints, branch, and resamples. Add a failed-admission test.

2. **Critical — Task 4:102–106.** Checking `anchor.status == "verified"` does not bind an imported draw to this protocol. `scripts/block_draw.py:135–142` supplies `protocol_sha256`, but Task 4 does not check it. **Repair:** compare the digest with the protocol bytes and verify H=A+144, headers, final hash, tips, and attestation binding. Test a valid draw from another protocol.

3. **Important — Task 3:86; Operation 5:211–212.** The tag precedes proof creation and upgrade. Committing the proof moves HEAD beyond the tag; leaving it uncommitted violates the clean-tree check. Later ledger changes cause the same problem. **Repair:** commit the upgraded proof before the final signed tag, then use a separate clean evaluation checkout and publication checkout.

4. **Important — Global Constraints:19; Operation 6:218; `scripts/revision_v2.py:842–845`.** The local H4 load contradicts the plan’s pod-only reader rule. Each pod then makes its own exclusion decision without consuming `h4.json`; different pods can use different effective manifests. Design 11 step 2’s H4 commit is also absent. **Repair:** define one permitted automated load procedure, commit the custody bundle in its separate clone, and bind every pod and the report to one recorded decision before evaluation episodes.

5. **Important — Task 2:69–72; Operation 3:197–198.** Comparator-only promotion cannot satisfy checks requiring all four systems and fixtures. Individual system outputs cannot satisfy them either. Also, fixture output has neither `smoke` nor budget fields (`scripts/tune_v2.py:142–148`), so “smoke false everywhere” cannot be checked as specified. **Repair:** define validated incremental promotion and a final completeness check; add fixture provenance fields.

6. **Important — Operation 4:203; `scripts/coverage_v2.py:65–80`.** There is no market selector: every `--pools` invocation runs every branch market. “One pod per coverage market” duplicates work. `--workers` is unused. Operation 3’s later commands also omit the chosen markets, allowing default `dev1` work after a development cut. **Repair:** add a market selector or use one pool invocation; pass the chosen branch and markets everywhere.

7. **Important — Operation 2:190–193; Operation 7:224; `scripts/benchmark_v2.py:33–68`.** The cost function prices fixed full-manifest counts and has no cut or coverage-branch input. Nothing implements choosing the smallest affordable cut or recalculating development cuts. A 25% pod allowance can also exceed the cap even when the base estimate passes. **Repair:** add branch-aware and cut-aware costing, include benchmark spend, and allocate capped pod budgets from the remaining balance. Specify pod sizes; benchmark, tuning, and coverage currently ignore worker counts. The capped benchmark is correctly placed before approval; later paid work must wait for the cost decision.

8. **Important — Operation 7:226; `scripts/revision_v2.py:716–730`.** The local evaluation command is not a read-only check: missing or stale records trigger episodes. **Repair:** add a verification-only command that refuses missing, stale, or foreign records and cannot run an episode.

9. **Important — Task 5:119–120; Task 6:147; `scripts/revision_v2.py:179–182,555–568`.** `accept` validates frozen search inputs, not evaluation, cross, and doubling records. Catalog provenance also uses current HEAD, so reproduction at the later report commit conflicts with protocol-tag records. **Repair:** reconstruct expectations from the registered tag and verified instances; validate every consumed record’s stage, provenance, dependencies, seeds, dimensions, and finite values.

10. **Important — Task 5:121–136.** Q1 strata and Q4 p-value directions are correct, and the decision helpers apply kappa. The report specification is incomplete:

   - Q1 needs estimates, calibrated simultaneous intervals at tail `kappa×0.05/8`, and descriptive headline/per-market results.
   - Q2 needs paired **per-seed contrasts** before bootstrapping; cell means alone cannot supply the required intervals. Include the fixed-bank envelope required by design 6.6.
   - Q3 needs welfare intervals, attacker gains, and the exact “no feasible candidate found” case.
   - Q4 needs “generalisation not established” when undecided, plus reported bounds.
   
   **Repair:** specify these outputs and independent numerical test oracles. Also specify secondary whole-system and repair comparisons.

11. **Important — Task 5:129–131; Task 4:103.** Missing records are tested, but scheduled doubling results that mark cells incomplete are not connected explicitly to unanswered questions. The report does not consume `confirmatory=False`, so late publication can retain confirmatory wording. **Repair:** define each question’s required cells and checks; propagate incomplete status and the draw’s nonconfirmatory label throughout the report.

12. **Important — Task 7:162–165; `scripts/revision_v2.py:747–775`.** **Accept the full-freeze ruling:** priority cannot waive the freeze requirement. Reject the claim that sorting `build_jobs` establishes the stated order: the runner partitions jobs into family and objective waves, which can put lower-priority work before Q1/Q4 X7 searches. The proposed test also supplies only `CRED`; whole-system jobs require tuned parameters (`revision_v2.py:121–123`). **Repair:** state dependency-constrained priority, test actual dispatch order, and supply complete parameters.

13. **Important — Task 6:147–149; Operation 9:237; `.gitignore:12`.** Results are ignored, and no operation packages or force-adds them. The fresh-clone artifact check can therefore lack all evaluation records and reports. **Repair:** define artifact inclusion, include paper sources and H4, verify tag signatures, and test the assembled fresh-clone artifact.

14. **Important — Planned tests, Tasks 3–7.** Several tests can pass with plausible wrong implementations: round trips can share the same omission; synthetic reproduction can repeat the report’s error; the H4-exclusion test checks `effective` without runner integration; the priority test checks sorting without dispatch; report tests omit Q2/Q3 numerical oracles and incorrect tails/kappa. **Repair:** add independent expected outputs and mutation cases for these failures, failed admission, late publication, and foreign evaluation records.

15. **Minor — Task 1:44,50; Operation 6:217.** The test uses `h4_check --smoke`, but the stated CLI omits that flag. The block reader writes its output without creating its parent (`scripts/block_draw.py:142`); the runbook never creates `results/v2/draw`. **Repair:** specify the flag and directory creation.

DECLINED TO JUDGE: Live pod prices, performance, launcher internals, external publication services, and tests not executed. No paid APIs were called; `sealed/` was not read. All design 11 steps 2–9 have named operations, but steps 4–9 cannot reliably complete with the stated interfaces and Tasks 1–7 alone.

CONFIDENCE: 0.96.