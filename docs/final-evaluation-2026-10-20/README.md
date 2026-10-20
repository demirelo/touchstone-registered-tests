# Final evaluation record (2026-10-20)

Lock `lock-2026-10-17` with amendments 1 to 4 (latest tag `lock-2026-10-17-amendment-4`, commit 36e66c7); freeze `freeze-2026-10-18` (commit 231c284); unseal commit a592f10 (sealed bundle hash a97e621b… verified against the lock). The proposed rule is R3 (amendment 3): allocation A, targeting T1, tolerance 0.16, ban L = 10. Evaluation seeds: the first 40 of the 60 sealed final-evaluation seeds (H2, H3); the first 10 for H1.

## Verdict (`verdict.txt`, `verdict.json`; command in `docs/lock-runbook.md`, verified against the amendment-4 tag and the freeze tag)

**Original claim: FAIL.** Confirmatory family H2 only.

| Clause | Result | Bound |
|---|---|---|
| Rule clause H2, gross efficiency | PASS | lower 0.9942 (threshold 0.90) |
| Rule clause H2, gain | PASS | upper 0.0436 (threshold 0.30) |
| Rule clause H2, audit spend | PASS | |
| Baseline clause B2 | FAIL | loss difference −0.0015, gain 0.0078 |
| Baseline clause B3 | FAIL | loss difference −0.0037, gain 0.0467 |

The baseline clause failure was predicted at amendment 1: against the sealed attackers at beta 0.05, B2 and B3 already hold the gain near zero, so R3 cannot beat them by the locked margin.

**Amended claim (amendment 1, H3 public identity-replacement stress test): PASS.**

| Part | Result | Bound |
|---|---|---|
| H2 rule clause gate | PASS | |
| gain_diff sides admitted (extension report) | yes | |
| H3 absolute, gross efficiency | PASS | lower 0.9980 |
| H3 absolute, gain | PASS | upper 0.0719 |
| Paired gain reduction vs B2 | PASS | lower 98.75 % bound 0.487 (threshold 0.10) |
| Paired gain reduction vs B3 | PASS | lower 98.75 % bound 0.276 (threshold 0.10) |

Limitation, as registered: proxy admission on development distributions with B3 standing in for R*; this is not nominal coverage for comparisons involving the selected R3.

## Per-cell results at the claim budget (beta 0.05, median position, 40 fresh seeds; `figures/figure_data.csv`)

| Rule | H2 mean gain | H2 attack efficiency | H3 mean gain | H3 attack efficiency |
|---|---|---|---|---|
| B1 | 0.409 | 0.869 | 0.409 | 0.869 |
| B2 | 0.006 | 0.969 | 0.570 | 0.870 |
| B3 | 0.043 | 0.995 | 0.353 | 0.974 |
| R3 | 0.041 | 0.995 | 0.071 | 0.999 |

Reading: against the sealed adaptive attackers (H2), R3 matches B3 and B2 within noise; against identity replacement (H3), B2 and B3 lose 0.57 and 0.35 of the honest surplus while R3 loses 0.07.

## H1 (sealed LLM attacker, exploratory; `h1/`)

Model `claude-opus-5-5`, T = 100, 10 repetitions per cell, sealed prompt. Comprehension: B1 9, B2 8, B3 8, R3 8. Zero invalid repetitions in every cell. Median gain [min, max] and median attack efficiency:

| Rule | beta 0.02 | beta 0.05 | beta 0.1 |
|---|---|---|---|
| B1 | +0.428 [+0.425, +0.430], 0.870 | +0.428 [+0.425, +0.430], 0.870 | +0.428 [+0.425, +0.430], 0.870 |
| B2 | +0.037 [+0.008, +0.096], 0.967 | −0.036 [−0.053, −0.005], 0.969 | −0.068 [−0.087, −0.029], 0.970 |
| B3 | −0.028 [−0.040, −0.021], 0.987 | −0.051 [−0.060, −0.042], 0.989 | −0.060 [−0.067, −0.054], 0.983 |
| R3 | +0.004 [−0.005, +0.038], 0.980 | −0.051 [−0.059, −0.038], 0.991 | −0.060 [−0.065, −0.047], 0.988 |

H1 is exploratory under the registered coverage consequences (proxy bound not admitted), and H1 against R3 is INCONCLUSIVE by the registered rule because R3's audit selection is not expressible in the description vocabulary; the per-cell `inconclusive: false` flags record invalid repetitions only. The twelfth cell (R3, beta 0.1) was run under amendment 4 (cap lifted once from 300 to 330 USD after the other eleven cells were seen; pre-resume copy in `docs/amendments/h1-pre-resume-2026-10-20/`). Amendment-4 completion checks: 12 cells, 10 repetitions each in order, `partial` empty, `cost_cap_usd` 330.0, cumulative spend 328.58 USD over 39,094 unique calls.

## Run history and deviations (all recorded; none touches a registered artifact)

1. H1 stopped at 205.33 USD when the account's credit ran out (2026-10-19 20:50); resumed from the cache.
2. One accidental duplicate H1 launch on 2026-10-19 (about two minutes, about 1 USD), killed; the claim check and figures made at 15:15 that day used partial H1 and are superseded by this record.
3. H1 stopped at the locked 300 USD cap with 11 of 12 cells (2026-10-20 07:55) → amendment 4 (Sol and Astra consensus after a round-1 rejection of a wrong statement about the cap's origin; signed tag; OpenTimestamps proof).
4. On 2026-10-20 a premature resume before the amendment-4 tag existed was stopped during cache replay, before any paid call (ledger unchanged at 299.89 USD); a second concurrent launch was stopped after 19 seconds, also before any paid call.
5. A session restart killed the resumed run at 307.85 USD; a credit stop followed at 319.99 USD; each resume replayed the cache, so no paid call was repeated.
6. The first claim-check attempt on completion was refused because the checking shell lacked `TOUCHSTONE_IDENTITY_SALT`; rerun with the sealed salt path, unchanged inputs.

## Figures

`figures/figure1_gain_vs_audit.png` (gain against audit budget, H2 and H1), `figures/figure2_efficiency_quadruple.png` (honest, reference, clipped, and attack efficiency), produced by the frozen `scripts/plot.py`.
