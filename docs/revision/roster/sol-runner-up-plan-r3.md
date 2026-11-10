VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `docs/revision/followup2/guards.py:139`, `:152`; `runnerup_v2.py:211`.** The round-2 evidence correction remains incomplete. An in-memory probe accepted reset gates with unrelated stages and cells, inventories without record hashes, and an anonymous doubling `{"pass": true}`. Require the named headline F111 D2 reproduction and fresh0 F111 D2+H3 doubling checks. Verify their inventory hashes and current input/code bindings. Retain the pod’s bit-identity requirement. Add refusal tests for unrelated, incomplete, and stale evidence.

2. **Block pod — §2; `docs/revision/followup2/guards.py:119`.** Environment matching omits SciPy, CMA, BLAS, and LAPACK, although the inventory records them. A probe accepted changes to all three numerical-library fields. Compare the complete recorded numerical environment before accepting pod evidence.

3. **§2; `docs/revision/followup2/runnerup_v2.py:122`, `:345`.** Check copied bank hashes before reference construction on resumed execution. `--stage reference` currently reaches the frozen reference builder without that check; `_required()` rejects a changed bank only during the later freeze. The round-2 request covered both reference construction and acceptance. Add a refusal test for this resumed path.

4. **None — §§1, 3–4.** The estimand answers sensitivity to this specific development-selected alternative. The plan states its limits, fixes expectations before new outcomes, matches base/doubled contrasts, distinguishes unavailable results from failures, and correctly qualifies nominal intervals and deferrals.

5. **None — §5 and remaining round-2 checks.** The benchmark reproduces 17.65 core-hours and USD 1.99 billed cost. The USD 3 reservation matches the admission cap; allocation time and prior spending are supported. All 12 specifications, pairings, and budgets passed checks; all 108 original bank hashes matched. Freeze acceptance now checks copied banks directly against original hashes. The convergence addition selects 19 cells, including six nesting cells, with the embedded doubled incumbent from round 2.

6. **None — validation scope.** Nineteen tests requiring no file writes passed. The full 65-test suite and smoke execution were not rerun under this read-only review.

CONFIDENCE: 0.98.