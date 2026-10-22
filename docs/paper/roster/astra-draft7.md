VERDICT: reject

CORRECTIONS:

1. In `paper/main.tex`, Appendix “Parameters and definitions,” replace “median ($\lfloor N/2 \rfloor$-th)” with “median (one-based rank $\lfloor N/2 \rfloor+1$).” The code uses `order[cfg.N // 2]`, which selects the sixth provider for \(N=10\).

2. In the same appendix, replace the unrestricted statement “Bids are…” with: “The D1 and D2 policies, including D2+H3 and their truthful twins, use bids $(1+w)(a_i+b_iq)$ with $w\in[0,2]$. Honest-max bids its production cost. The general offer interface permits any finite nonnegative bid.” The current sentence incorrectly makes a search-family restriction a market-wide restriction; `Offer` and the H1 action parser permit a wider domain.

3. Correct the customs statements in the abstract, introduction, and related work. Replace “customs practice” with “customs guidance”; replace the two claims that administrations select or verify all new-importer declarations with: “Walsh recommends selecting every declaration from a new importer for verification during an initial period.” The source gives a recommendation, not evidence that administrations universally implement it. [Walsh, Chapter 5](https://www.elibrary.imf.org/display/book/9781589062115/ch05.xml)

4. Replace the abstract sentence beginning “A predecessor without the priority phase…” with: “The predecessor without the priority phase reached a development H3 gain of 0.073, compared with R3’s 0.070; the separate contribution of priority is not identified.” In the discussion, replace “newcomer-priority auditing with pacing reduces” with “R3’s complete audit-selection and pacing bundle yields a reduction in.” The predecessor result supports the stated lack of identification; it does not isolate the causal contribution of the shared components.

5. In the conclusion, replace “The prospectively registered protocol that produced these findings, including its amendments and its failures, is part of the contribution” with: “The staged-registration record, including changes informed by development results, the original claim’s failure, and the final evaluation on fresh seeds, is part of the contribution.”

6. In `docs/theory/reset-deterrence.md`, section 5, replace “Lemma 2b says that under T1 the established hazard $q_E$ of a replacement identity is itself high” with: “Lemma 2b gives a lower bound on audit exposure under T1; the failure hazard also depends on shading and can remain small. With six audits at truthful effort, $q_E=1-(1-d_0)^6\approx0.004$.” This rejected claim remains in the supplement despite its correction in the paper.

7. In `paper/main.tex`, “Checks,” replace the B2/B3 interpretation through the reference to Corollary `cor:uniform` with: “In the tested B2 and B3 cells with positive shading, replacement yields more profit than waiting. This is consistent with removal of the ban’s continuation cost, but it does not isolate that effect: the diagnostic policy also returns to honest effort for ten rounds after each reset.” Retain the reported numbers separately. The current main-text interpretation lacks the qualification already added to both supporting documents.

8. In related work, replace “Crowdsourcing platforms examine new workers with gold tasks before continuing budget-sensitive evaluation” with: “CrowdEval requires an initial gold-task screening test and then adjusts the balance of gold and peer evaluation to control evaluation cost.” The cited paper supports this particular framework, not a general statement about platform practice. [Qiu et al., section 2](https://www.ifaamas.org/Proceedings/aamas2018/pdfs/p1486.pdf)

REASON: Most triage corrections are applied, including the stronger replacement condition, the equality condition, the threat model, the README erratum, and the limits on coalition and entry-cost results. The provider parameters and first-best definition match the code, but the median rank and bid-domain statements do not. The predecessor result is reported correctly, but attribution and registration wording remain inconsistent across sections. The customs and crowdsourcing statements exceed the scope of their sources. The previously accepted proof conditions, H1 separation, tier boundaries, headline results, and coverage qualifications remain intact. No files were changed, no paid API calls were made, and `sealed/` was not read.

CONFIDENCE: 0.94
