# Response to the round-9 (fresh) external review

Thank you for a careful review that reproduced every headline number. We made the text changes and the analyses on
existing records. No simulation was run, and no registered estimate or decision changed. Table numbers refer to the
revised draft (`main.pdf`, 29 pages).

1. **Doubled-search winners (problem 1).** New Table `tab:ph-doubled` gives, per market, C*-R3 (both families) and
   B3-R3 with the frozen winners and with the doubled-search winners, on the same seeds and frozen references
   (`posthoc_v2.py doubled`, tested; it refuses a doubled evaluation on other seeds). Section 9 now says that fresh3
   changes from -0.038 to 0.015 and the pooled differences become 0.030 (D2+H3) and 0.024 (X7-SC); no decision is
   recomputed. Your values match ours.
2. **Value of replacement (problem 2).** The caveat now sits at the first definition of the gain (Section 3). The
   reset-on versus reset-off experiment needs compute. Updated 2026-11-10: the author first deferred it, then approved it (cap 10 USD;
   plan `docs/revision/reset-experiment-plan.md`). It runs the 18 D2 cells that budget cut 3 removed; no result is in this version.
3. **Margin and comparator (problem 3).** Section 9 prints the absolute mean gains (0.086 and 0.065 under D2+H3; 0.091
   and 0.067 under X7-SC), ties "material" to the registered margin and says the margin is not a buyer-indifference
   estimate. Section 4 names the selection objective and the runner-up.
4. **Uncertainty (problem 4).** The fresh1 extreme Q2 intervals were already disclosed at the start of Section 9. The
   per-market estimates appear in Figure 1 and the new doubled table.
5. **Lottery (problem 5).** Section 9 now points to the fixed interior weights of Table `tab:ph-welfare-sens`.
6. **Audit dues (problem 6).** Section 1 now says the lemma bounds audit exposure, not a monetary charge, and that the
   bound can be zero. New Table `tab:ph-honest` gives the registered honest-replacement diagnostic, computed from unrounded report values (audited
   share 1.000 / 0.917 under R3, 0.428 / 0.161 under C*, 0.250 under B3; profit per round and false refunds), and Section 9
   states the burden. The Lemma proof now uses i.i.d. continuous keys (exchangeability).
7. **Corollary (problem 7).** The statement adds the second condition (every post-failure continuation is available
   after no failure); the proof gives both inequalities and says why B2 and B3 satisfy them, and names a rule that would
   not.
8. **Exemptions (problem 8).** Unchanged in this revision; the caption already names the six exemptions. Your 1/2/15
   sensitivity is noted for the supplement.
9. **Related work.** Gilpatric, Vossler and Liu (2015) is cited and contrasted (compliance rank versus identity age).
10. **Table 10 (tab:q4).** The decision column now marks the inherited flags of fresh0 and fresh3.

Not done: the venue cut (supplement split and new figures), and the compute experiments.
