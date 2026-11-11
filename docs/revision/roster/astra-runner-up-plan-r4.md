VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `guards.py:159`.** Round-3 evidence validation remains incomplete. An in-memory probe accepted evidence without evaluation records, doubling records, or copied inputs, and with unrelated search provenance. The guard verifies only the gate/input manifest hashes and search budget. Require the supporting records, verify their inventory hashes, provenance and dependencies, and recompute `compare()` / `compare_doubling()` against registered records. Add refusal tests for missing and changed supporting records.

2. **Block pod — §5; `guards.py:111`; `results/pods/reset_pod.sh:49`, `:103`, `:108`.** Failed-attempt accounting does not match the stated launcher. The driver expects `pod start end price`; the launcher writes `pod timestamp start/deleted`, omits prices, and truncates the file on launch. A probe confirmed that the parser rejects this format. Implement and test one persistent format, preserve earlier spending across relaunches, and transfer the reconciled record to the pod before driver admission.

3. **Block pod — §§5–6; `runnerup_v2.py:359`; `results/pods/reset_pod.sh:128`.** Make the launcher’s stop contract executable. The proposed `--stage all` command never checks the launcher’s STOP file or soft deadline between its internal stages. Use separate stage invocations with deadline checks, or add those checks to the driver. Test the adapted launcher, including attempts transfer, allocation time, price, retrieval, and deletion. The watchdog’s 1.3× exception is now stated.

4. **§2, pre-spend validation.** At inspection, both Run A gate directories lacked `gate.json` and `inventory.json`; Run B lacked final gate records. These checks remain incomplete, not failed. Require completed Mac evidence before allocation and bit-identical pod evidence before runner-up searches.

5. **None — remaining round-3 corrections, §§1–4 and benchmark arithmetic.** Resumed reference construction now checks banks; environment comparison includes SciPy, CMA, BLAS and LAPACK. Live checks passed for 12 specifications, pairings, budgets and dependency sets, plus 108 bank hashes. The bounded estimand, matched base/doubled contrasts, advance expectation, nominal conditional intervals and deferrals are appropriate. Cost reproduces: 17.65 core-hours, USD 1.99 billed estimate, USD 3.00 reservation. Forty read-only test cases passed with optional plotting disabled; the full suite and smoke run were not rerun.

CONFIDENCE: 0.98.