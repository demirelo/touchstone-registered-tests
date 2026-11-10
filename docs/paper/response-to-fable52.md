# Response to the Fable 5.2 fresh review (2026-11-10)

We checked every claim against the records before changing the paper (`docs/paper/fable52-triage.md`). Changes are
analyses on existing records and text; no simulation was run and no registered estimate or decision changed. New
simulations that the review asks for are listed at the end; the author decides on them.

1. **"Equivalent" and the margin (problem 1).** Partly accepted. Treating the six markets as a sample, the per-market
   differences give a t interval of [-0.013, 0.054] under D2+H3 (5 of 6 positive) and [0.005, 0.044] under X7-SC; with
   the doubled-search winners, [0.014, 0.045] (all 6 positive). The paper now says that the registered intervals measure
   seed uncertainty in six fixed markets and that this analysis does not establish the category for the neighbourhood,
   gives the relative difference (0.319), and calls the margin "pre-set materiality margin". We do not accept that the
   margin was set after development: it is in the design accepted on 2026-10-22 (commit 2a288f5); the development values
   d = 0.027 and 0.038 came with the comparator on 2026-10-28 (commit c5227a0).
2. **The two Q1 families (problem 2).** Accepted. In 10 of 12 Q1 cells the X7-SC winner is the embedded D2+H3 winner
   with identical gains; only fresh3 against C* and fresh4 against R3 differ (12 of 14 market-rule cells with the headline market, which
   explains most of Q3-a's zeros; you counted 11 of 14). The abstract, contributions, Q1 paragraph, and conclusion now say
   that the two families are close to one test.
3. **Search strength (problem 3).** Accepted as text and an analysis: 21 of 98 doubling checks are flagged, fresh-market
   factorial cells outside Q1 and Q4 have no doubling check, and with each rule's strongest training-selected family the
   pooled C* minus R3 difference is 0.031 (0.070 on fresh1). Searches to convergence need compute (below).
4. **Honest churn (problem 4).** Accepted as a limitation, stated in the model, the remark after Lemma 2, the abstract's
   scope, and the limits. A new identity marks a replacement history, not dishonest delivery. An honest-churn arm needs
   compute (below).
5. **Comparator selection (problem 5).** Accepted, with a correction found in internal review: every configuration's
   score is its efficiency margin, so the selection was on gross efficiency in effect. Only the two best were rechecked
   at full budget; both scores were decided by D2 at dev0 (C* 0.103, C-thr(12) 0.098), while under D2+H3 the runner-up
   left the lower development gain (0.076 against 0.097 at the headline market, 0.018 against 0.038 at dev0). A new
   appendix table, Table 24 (tab:comparator-dev), lists all twelve configurations with their scores and deciding cells.
   The paper says so in Section 4, the Q1 paragraph, the abstract, and the limits. Running C-thr(12) on
   the fresh markets needs compute (below).
6. **Corollary 1 (problem 6).** Accepted in part: the abstract, the introduction, and the corollary statement now name
   the conditions (honest rivals whose play does not depend on the focal identity; re-entry before the next allocation).
   The corollary stays a corollary; its proof shows both inequalities for B2 and B3.
7. **Lemma 2 and Theorem 1 (problem 7).** Accepted: "audit dues" removed; age defined from the first offer; jobs are
   audited by age group, newest first, with k defined; an identity that offers but wins no jobs still ages; Theorem 1 is
   marked as not used by any reported result. Moving it to a supplement belongs to the venue cut.
8. **Contribution (iii) (problem 8).** Accepted: the registered W1 search found no profitable welfare attack against R3
   (zero estimated gain; the doubled W1 winners are truthful delivery with the replacement option on). The mixture is
   described as arithmetic on two components; its paragraph is shortened and removed from the abstract, and contribution
   (iii) is now the honest-replacement cost of R3's targeting.
9. **Priority phase (problem 9).** Accepted: once newest-first targeting is in place, the priority phase changes the gain
   by only -0.001 (abstract, contributions, Q2).
10. **Statistics (problem 10).** Covered by items 1 and 3; moving the calibration detail after the results belongs to the
    venue cut.
11. **Process facts (problem 11).** Accepted: the H4 session (started by the author, resumed by the executor after a
    restart without reading its log or bundle, bundle committed in a separate clone, only its hash in the protocol);
    the dependence of Q1-a, its alternative, and Q1-d on the same Q1 categories; Q3-e's margin.
12. **Related work.** Added Harrington (1988), Dellarocas (2005), and Golle and Mironov (2001), each checked on Crossref.
13. **Presentation.** The abstract is rewritten around four plain findings (328 source words, from about 490); the
    12-page venue version is a separate task.

**Simulations the review asks for:** the author approved all of them (ledger: follow-up cap 22 USD). Each has a plan
under internal review: an honest-churn arm (`docs/revision/churn/`), the runner-up comparator C-thr(12) on the six fresh
markets and searches to convergence on the 14 flagged profit cells (`docs/revision/followup2/`). No result is in this
version.
