VERDICT: reject

FINDINGS:

1. **Important — Tasks 7/10/12: conflicting timing records and a circular hash.** `docs/superpowers/plans/2026-10-27-revision-part-a2.md:126`, `:128`, and `:183` require `seconds` and the same timing record in `check.json` and printed output. Line 210 replaces that schema with `h4_seconds`, `x7_seconds`, and `bundle_sha256`. But `sim/h4_loader.py:14–22` includes `check.json` in the bundle hash. Writing the new record into that file changes its own claimed hash; retaining the old schema breaks the new consumer. **Repair:** define one timing payload without the bundle hash, write it into `check.json`, then compute the hash and attach it only to the exported record. Update all three tasks and test actual producer-to-promotion output.

2. **Important — Task 12: the handoff lacks independent expected identifiers.** The plan at `:211` requires comparison with the “protocol’s H4 hash input” and promoted defenders’ commit. However, `_decision_h4` at `:178` receives neither identifier, and the specified command supplies neither. The protocol is created later (`docs/superpowers/plans/2026-10-25-revision-operations.md:169–174`). Promotion therefore cannot perform the specified independent check from the stated inputs. **Repair:** supply an explicit author-recorded commitment file or arguments containing the expected bundle hash and defender commit. Verify the defender files against that commit, separately from `same_code`. Test the real command before a protocol exists, including wrong defender and bundle identifiers.

3. **Important — Tasks 10/12: revised spending gates are incomplete.** The plan at `:179` specifies evaluation-cap stopping but no stop when actual development spend plus remaining coverage exceeds 12 USD. Line 211 places renewed total-cost approval in `lock_v2.build`, after paid coverage. This permits coverage to start after an over-cap forecast or before approval of a revised total above 40 USD. Design requirements are explicit at `docs/superpowers/specs/2026-10-22-revision-program-design.md:513–523`. **Repair:** stop on development above 12 USD without changing frozen defenders; require renewed approval before coverage when the revised total exceeds 40 USD. Test both boundaries.

4. **Important — Task 9: refusal can still terminate the report.** The plan at `:160` catches `NonfiniteStatistic`, but `sim/intervals.py:118–125` rejects nonfinite samples with ordinary `ValueError`. Two individually finite rule arrays can overflow during the paired subtraction (`scripts/report_v2.py:80`), so `sample()` raises before the new mean/statistic guards run. The specified catch then misses it. **Repair:** define a common numerical/sample refusal exception, or explicitly catch these existing sample errors per test. Add a report test with finite operands whose difference overflows, alongside the bootstrap-overflow test.

5. **Important — Task 9: partial withholding does not preserve the multiplicity denominator explicitly.** The plan at `:160–164` requires the other Q1 test to remain available after one fails. Existing code derives both Holm size and interval size from supplied tests (`sim/decisions_v2.py:31–33`; `scripts/report_v2.py:82`). Removing the failed test would change Q1 from two slots to one: a calibrated p-value of 0.03 would become significant. **Repair:** retain both registered slots, substitute p=1 for the unavailable test, mark it undecided, and retain m=2 intervals. Add this boundary case; retaining unrelated output alone does not test it.

Sol R1-1: resolved.  
Sol R1-2: resolved.  
Sol R1-3: resolved.  
Sol R1-4: resolved.  
Sol R1-5: resolved.  
Sol R1-6: partly resolved — findings 4–5.  
Sol R1-7: resolved.  
Sol R1-8: resolved.  
Sol R1-9: partly resolved — finding 3.  
Sol R1-10: resolved.  
Sol R1-11: partly resolved — findings 1–3.  
Astra R1-1: resolved.  
Astra R1-2: resolved.  
Astra R1-3: resolved.  
Astra R1-4: resolved.  
Astra R1-5: resolved.  
Astra R1-6: resolved.  
Astra R1-7: partly resolved — findings 4–5.  
Astra R1-8: resolved.  
Astra R1-9: resolved.  
Astra R1-10: partly resolved — finding 3.  
Astra R1-11: partly resolved — findings 1–3.

CONFIDENCE: 0.92.