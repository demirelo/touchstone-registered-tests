VERDICT: accept-with-caveat

CORRECTIONS:

1. `main.tex:240`, `rs_ref_dg`, `rs_ref_s`: Describe S = 1.050 as a sensitivity calculation that adds the Mac replacement effect to the stored Linux gaps. It is not a Linux re-evaluation with non-replacing references. The recomputed shift is +0.000544133 for **both** G(D2+H3) and G(D2), giving S = 1.049569. The C*−R3 shift differs: −0.001345278. State this scope explicitly. Prefer printing 0.0005; the current site prints 0.001. The maximum validation discrepancy, 0.007373, is comparable to the maximum replacement effect, 0.008902. Problem 2 is therefore addressed as a qualified sensitivity check.

2. `docs/revision/posthoc/reset_reference/ref_resets.py`: Add reproducible aggregation for the committed `cells`/`summary` structure. The script currently writes only cell rows; it does not generate the summary or S. Correct its opening description: it records validation differences rather than requiring equality. Reset counting and both disabling mappings are correct: X7-SC uses `h_R=T, lambda=1`; D2+H3 uses `x=0`. The stored summary recomputes correctly, including 17/18 references with resets.

3. `main.tex:21,341`: Replace “R3’s measured advantage lies in the replacement channel” with “most of the measured B3−R3 advantage disappears in the prescribed searches when attacker replacement is disabled.” The current wording turns a search-dependent comparison into a stronger attribution. In the conclusion, specify “neither **pooled mean gap** is distinguishable from zero using the exploratory market-level t intervals.”

Problems 1 and 3–7 are resolved. Independent recomputation confirms the intervals, sign counts, leave-one-out range [0.967022, 1.092676], flags 3/18 with maximum 0.044089, nesting failures, fresh0 sign change, and table values. All 26 new number sites and kinds match their sources; eight targeted tests pass. The revised S explanation correctly separates seed uncertainty from market variation. The ledger’s commit times and gate hash match the records.

CONFIDENCE: 0.95.