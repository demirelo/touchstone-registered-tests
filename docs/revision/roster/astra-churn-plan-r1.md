VERDICT: reject

CORRECTIONS:

1. **Blocker — §3; `sim/reference.py:61`, `sim/reference.py:87`, `scripts/revision_v2.py:894`.** Copied menu candidates retain cached no-churn profits. `select_reference` reuses them when seed counts match, so the production doubling diagnostic mixes environments. Its `reference_change` also subtracts the stored no-churn reference score. Clear candidate caches and recompute both sides under churn. Add a five-training-seed regression test; the two-seed smoke test misses this defect.

2. **Blocker — §3(c); `churn_v2.py:157`; `reset_followup_v2.py:343`.** Implement the standalone reproduction gate before launch. The churn driver has no gate command, and the existing comparator reads the same record ID from both directories; churn adds a suffix. Map IDs explicitly, preserve dependency checks, save the gate result, and stop dispatch on failure. Test multiprocessing injection. Search, evaluation, and doubled attack episodes otherwise receive churn correctly; separate IDs and output directories protect registered records.

3. **§3, churn model.** Independent replacement is a fair controlled test of the age concern. It preserves capacity and provider quality while changing identity age. Label 0.01 and 0.05 as illustrative sensitivity rates, corresponding to mean identity lifetimes of 100 and 20 rounds. The fresh-window percentages do not establish that “newest” becomes uninformative most of the time. Measure that claim or remove it.

4. **§§2–3, references.** Frozen-reference reuse is acceptable for the stated estimand. A weaker reference can increase measured gain; unequal reference losses can move either rule contrast in either direction. Distinguish cheap reselection among fixed candidates from expensive regeneration of all menus. Report the corrected diagnostic without claiming it bounds held-out bias.

5. **§§5–6.** Compare base with base and doubled with doubled no-churn results. The stored doubled C*−R3 baseline is approximately 0.02962, versus 0.02072 for base. State that bootstrap intervals condition on markets and selected policies. Keep the peek disclosure; expectations remain exploratory.

6. **§§4–6; `churn_v2.py:144`.** Diagnostics use only base winners, but expectation scoring requires both search budgets. Add doubled-winner diagnostics or limit expectation 4 explicitly. Define market pooling. Audit exposure alone does not establish financial cost.

7. **Blocker — §§7–8; `churn_v2.py:165`.** Specify workers, gate costs, serial diagnostics, budget reservation, and a timed shutdown within $7. The 39.8-core-hour estimate is consistent, but default one-worker execution alone implies about $22.3 in pod charges.

CONFIDENCE: 0.97.