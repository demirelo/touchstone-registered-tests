# Decision brief: amendment 4, a one-time lift of the H1 cost cap (the repository is your working directory; read-only; no paid APIs; reasoning effort high; under 900 words)

## Situation
The registered study is at its last step. The sealed H2 and the public H3 evaluations on 40 fresh seeds are done and their verdict is recorded (`results/verdict_no_h1.json`: original claim FAIL, amended claim PASS). The H1 token run (sealed LLM attacker, 12 cells = 4 rules x 3 budgets, 10 repetitions each) stopped on 2026-10-20 at the locked cumulative cost cap of 300 USD (`experiments/locked.yaml`, `h1.cost_cap_usd`) with 11 of 12 cells complete and the cell `proposed|0.1` partial. `scripts/check_claim.py` refuses a partial H1. H1 is exploratory under the registered coverage consequences (`coverage_consequences: h1: exploratory`), so it cannot enter a registered verdict. The cap was set from the token pilot's projection and is excluded from the lock's bound hash as a measured figure (`sim/locked.py`, around line 48 to 54). The measured cost per complete proposed-rule cell is 28.4 to 29.9 USD; the last cell's completed calls are cached and replay free, so finishing it costs under 30 USD.

The author has decided to lift the cap by a registered amendment rather than report 11 of 12 cells. The draft is `docs/amendments/2026-10-20-amendment-4.md`. Read it, `docs/amendments/2026-10-18-amendment-3.md` (the previous amendment's form), `experiments/locked.yaml` (the `h1` block and `coverage_consequences`), `sim/locked.py`, `sim/claimcheck.py` (`verify_h1_summary`, `evaluate_claim`, `h1_proposed_reason`), and `scripts/h1.py` (the `--max-cost-usd` option and the cumulative ledger). Do not read `experiments/cache/` contents or `results/h1_final/h1_rows.csv` beyond what the draft already states.

## Questions
1. Integrity: is a post-hoc cap lift for an exploratory, pre-registered 12-cell table, decided after seeing 11 cells, acceptable with the draft's disclosure and reporting rule? If not, what exact text or condition makes it acceptable, or should the study instead report 11 of 12 cells?
2. Mechanics: is the draft correct that nothing in the verifier compares the summary's `cost_cap_usd` to the lock, that the resumed command with `--max-cost-usd 330` replays the cache and pays only for the remainder, and that the registration touches `docs/` only? Name any file the draft forgets.
3. The number: is 330 USD (300 plus the costliest measured cell rounded up) the right constant, and is "no second lift" the right stopping rule?
4. Disclosure: is the disclosure sentence complete and honest? Propose exact replacement text if not.
5. Anything in the draft that is factually wrong against the repository.

## Output
VERDICT: accept | accept-with-caveat | reject (a reject must name a material factual, logical, safety, or verification failure with a checkable repair). REPAIRS: exact text edits to the draft, numbered, or "none". ANSWERS: one short paragraph per question 1 to 5. CONFIDENCE: 0 to 1.
