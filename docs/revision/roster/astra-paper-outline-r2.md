VERDICT: reject

CORRECTIONS:

1. **Numbers rule and step 1 — remaining S10/A10:** Add explicit result-site-to-report-path checks for prose, complete result-region coverage checks, and checks of included result files. Schedule tests for swapped existing macros, omitted regions, and included captions. Generated table specifications address table labels, but leave these cases open (`docs/revision/paper-v2/outline.md:19-25`, `docs/revision/paper-v2/outline.md:163-165`). Read-only, in-memory probes confirmed that the checker accepts an existing gain macro as the replication count, an unmarked result with incorrect numbers, and an included caption with a bare result. It checks path existence and marked blocks in only the supplied file (`docs/revision/paper-v2/numbers_v2.py:80-90`).

2. **Numbers rule — new specification mismatch:** Add statistic-specific formatting and a small-p-value regression test to step 1. The outline requires four significant digits for p-values (`docs/revision/paper-v2/outline.md:27`), but the formatter applies three decimal places to every float (`docs/revision/paper-v2/numbers_v2.py:31-35`). An in-memory probe rendered `0.0001` as `0.000`. Preserve nonzero p-values and apply the stated precision consistently.

3. **§8 — remaining A7:** Name the registered branch, `two20k`, and add both omitted qualifications: no miner selects the target block to influence this evaluation; a later reorganisation deeper than six blocks is unhandled and must be reported. The revision states the development markets and accepted-chain assumption, but omits these details (`docs/revision/paper-v2/outline.md:101-106`). The branch appears in `experiments/protocol-v2.yaml:10`; the qualifications appear in `docs/superpowers/specs/2026-10-22-revision-program-design.md:447-449`.

All other round-1 corrections are resolved at the outline level. Planned table generation, figure scripts, and prediction scoring are not treated as missing implementations.

CONFIDENCE: 0.96
