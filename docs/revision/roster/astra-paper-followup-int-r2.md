VERDICT: reject

CORRECTIONS:

1. **main.tex:335:** Restrict “positive on all six” to doubled **D2+H3** and the training-selected envelope. Doubled X7-SC remains negative on fresh3 (**−0.002394790**), so it is positive on only five markets. The current sentence follows a claim about both families and overstates the result.

2. **posthoc_v2.py:317–319:** Remove “missed a policy its family contains.” This round-1 correction remains unfinished. Main.tex:291 correctly describes evaluation discrepancies: training-selected winners need not retain their ordering on evaluation seeds, and selecting the better D2+H3 winner there favours D2+H3.

3. **main.tex:21,37,40,191:** Carry the corrected scope into the summaries. Replace “newest-first targeting does most of the work” with the symmetric finding that either targeting component alone accounts for most of the pooled reduction. Line 240 now correctly limits “adds little” to pooled, separately searched comparisons and reports the larger fixed-attack effects. At line 191, specify that the **neighbourhood ordering** remains unestablished; at line 40, qualify sign variation as applying to frozen searches.

4. **posthoc.json; sites.json; numbers_v2.py:** All new numbers and mappings reproduce. Direct priority: **−0.002881735** pooled for both families; fresh1 **−0.014709234**, fresh3 **−0.002581178**, four zeros. Nesting: **11/21** positive shortfalls; six exceed 0.005: fresh0/C* **0.006144**, fresh1/R3 **0.005939**, fresh1/C* **0.008411**, fresh3/C* **0.019877**, fresh4/R3 **0.005260**, headline/R3 **0.021141**. Envelope: **0.030634427**, interval **[0.009467449, 0.051801404]**. Honest relative profit: **−0.044196710**.

5. **main.tex:76,191,220,257,347:** Comparator screening, deciding efficiencies and score precision, honest-profit wording, subsequent audit bin, Q1 caption, welfare-loss qualification, and mixture interpretation address the corresponding objections. Development records and embedding provenance reproduce locally.

6. **main.tex:240,291,331:** Compute remains necessary for honest churn, fresh-market runner-up sensitivity, attack/reference convergence including unflagged and factorial cells, paired honest-profit uncertainty, and audit-budget/capacity sensitivity. The shorter venue version and complete external evidence packet remain open.

CONFIDENCE: 0.97.