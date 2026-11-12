# Honest-churn results and paper text: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

The churn arm (plan draft 6, `docs/revision/churn/churn-plan.md`, consensus before any churn search) ran on one pod: RUN OK, all records verified, pod deleted (`docs/revision/operations-ledger.md`, last section). Records: `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-churn/followup-churn/` (gate-p0, p0.01, p0.05; each with evaluate, doubling, diagnostics.json, inventory.json). Registered no-churn inputs: `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all` and `/Users/oemer.demirel/Projects/touchstone/results/v2/report/report.json`.

Files:
- Analysis `docs/revision/posthoc/churn_block.py` and tests `test_churn_block.py` (18 pass). Order: code and tests c15580d; input guard c398a97 after a first run on a wrong directory (lesson in `docs/revision/lessons.md`); first run on the registered inputs cd64fc3; output naming and table format in 2066cdd (statistics and expectations unchanged; check with `git diff cd64fc3 2066cdd -- docs/revision/posthoc/churn.json`).
- Result `docs/revision/posthoc/churn.json`; table `docs/revision/paper-v2/tables/posthoc_churn.tex`.
- Paper: `docs/revision/paper-v2/main.tex`, paragraph "Honest identity churn (exploratory follow-up)" and Table `tab:ph-churn`; numbers come from `churn.json` through `sites.json` (`ch_*`) and `numbers_v2.py` (two new kinds, two count leaves); `results/pods/paper_check.sh` passes.

Rerun command: `uv run --frozen python docs/revision/posthoc/churn_block.py --records <eval/all> --churn <followup-churn/followup-churn> --report <report.json> --posthoc docs/revision/posthoc/posthoc.json --out <tmp>.json --tables <tmp>`.

Check:
1. The analysis implements plan sections 2, 4, 5 and 6 exactly: estimand, pairing (one index vector per market shared by rules, rates, versions and no churn), pooling, sign counts, profit terms, the scoring rule of section 6 (met, failed, not established), and expectation 4's measure.
2. churn.json follows from the records (rerun it; the registered check must be ok).
3. Every sentence of the paragraph and caption is supported by churn.json and stays within the plan's limits (exploratory; the permissions after section 6; the churn model's caveats; the doubling flags; the illustrative rates).
4. Defects the tests miss.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
