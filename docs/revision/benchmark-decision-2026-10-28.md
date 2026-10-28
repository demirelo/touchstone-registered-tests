# Benchmark and cost decision (Operation 2, 2026-10-28)

The benchmark ran one cell of each kind and one coverage fixture on a 16-vCPU pod (0.56 USD per hour) at code commit 627a2de (design draft 7 implemented). It took 4.54 hours and cost 2.54 USD. The cost model then recomputed design 8.2's table from the measured timings, and the decision rule of 8.2 chose the branch and the cuts. Raw records: `decision.json`, `cost_table.json`.

## The decision (written once, by rule)

| Phase | Choice | USD |
|---|---|---|
| Development | branch `two20k`: comparator selection and tuning on the headline market and `dev0` only, coverage fixtures by the replacement design of 9.5, 20,000 seeds per market | 11.17 (2.54 spent, 8.63 to go) |
| Evaluation | 3 cuts (below) | 38.08 (37.08 + 1.00 H4 reserve) |
| **Total** | | **49.25** |

The rule takes the first development branch that fits the 12 USD cap (three markets cost 12.54, so the first branch fails) and the smallest cut whose evaluation cost fits the 40 USD cap. Any total above 40 USD needs the author's written approval. The approval has **not** been given.

## Measured against the design estimate

| | Design 8.2 estimate | Measured |
|---|---|---|
| Development, three markets | 8.0 USD | 10.00 USD to go (12.54 with the benchmark) |
| Development, two markets | not estimated | 8.63 USD to go |
| Evaluation, no cuts | 31.3 USD | 42.88 USD (+ 1.00 H4 reserve) |

## Each cut (design 8.2, applied in this fixed order; fresh markets only, the headline market keeps everything)

| Cut | Removes | Cells | Saves (USD) | Evaluation after (with H4 reserve) | Question affected |
|---|---|---|---|---|---|
| none | | 287 | | 43.88 | |
| 1 | whole-system cells (B3-t, R3-t, C*-t) on fresh markets | 18 | 0.39 | 43.49 | secondary whole-system comparison: headline only |
| 2 | H4 (sealed, independently authored family) on fresh markets | 18 | 3.12 | 40.37 | Q3: the independently authored part is headline only |
| 3 | D2 matched extras on fresh markets | 18 | 2.29 | 38.08 | Q2/Q3 descriptive extras: headline only |
| 4 | C*/S0 cells on fresh markets | 12 | 0.40 | 37.68 | Q1 descriptive side cells: headline only |

Q1 (C* versus F111, confirmatory) and Q4 (F000 versus F111, confirmatory) keep all their fresh-market cells under cuts 1 to 3.

## The options before the author

- **A. Approve as decided:** total up to about 50 USD, cuts 1 to 3.
- **B. Keep everything:** raise the evaluation cap to 44 USD before the lock (a design change); total about 55 USD.
- **C. Keep H4 on fresh markets only:** change the cut order before the lock (cut 3 and cut 1 first, then H4); evaluation 41.20 USD with the reserve, total about 52.4 USD, still above the 40 USD evaluation cap, so it also needs a cap change.
- **D. Stop** before the lock.

Every option other than A changes design 8.2 before the lock.
