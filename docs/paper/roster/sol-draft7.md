VERDICT: accept-with-caveat

CORRECTIONS:

1. In `paper/main.tex`, replace the abstract’s sentence beginning “A predecessor without the priority phase” with: “A predecessor without the priority phase reached development H3 gain 0.073, compared with R3’s 0.070; these results do not identify the priority phase’s contribution or separate targeting from pacing.”

2. In the discussion, replace the sentence beginning “In the tested market, newcomer-priority auditing” with: “In the tested market, R3’s age-based audit selection and pacing yield a best-found identity-replacement gain of 0.071, compared with B3’s 0.353, under separately searched attacks and references; the priority phase’s contribution is not identified.”

3. In the parameters appendix, replace “median ($\lfloor N/2 \rfloor$-th)” with “median (zero-based rank $\lfloor N/2 \rfloor$, the sixth provider in sorted order when $N=10$)”. The code uses `order[cfg.N // 2]`.

4. In the same appendix, replace the universal bid statement with: “For D1, D2, and D2+H3, bids are $(1+w)(a_i+b_iq)$, where $q$ is effort and $w\in[0,2]$; honest-max bids production cost. H1 permits any finite nonnegative bid.” The current wording incorrectly applies the parametrised families’ restriction to H1.

5. Correct the customs statements in the abstract, introduction, and related work. Replace “customs practice” with “customs guidance”; replace the introduction’s customs clause and the related-work sentence with: “Walsh recommends selecting all declarations of new importers for verification for a period.” The source gives a recommendation, not evidence that administrations follow it. [Walsh, Chapter 5](https://www.elibrary.imf.org/display/book/9781589062115/ch05.xml)

6. In `docs/theory/reset-deterrence.md`, section 5, replace “Lemma 2b says that under T1 the established hazard $q_E$ of a replacement identity is itself high” with: “Lemma 2b gives high audit exposure under its coverage conditions; the failure hazard also depends on shading and can remain small (about 0.004 at truthful effort with six audits).” The paper corrects this claim, but the supplement retains it.

7. In the paper’s Checks paragraph, replace “Under B2 and B3 replacement removes the ban’s continuation consequence while effort savings and refunds still vary with shading” with: “Under B2 and B3, effort savings and refunds vary with shading in the tested resetting policies”. Add: “The diagnostic policy plays honestly for ten rounds after each reset, so the reset-versus-wait comparison does not isolate the ban’s continuation effect.”

8. In the conclusion, replace “The prospectively registered protocol that produced these findings, including its amendments and its failures” with “The staged-registration protocol, including its development-informed amendments and reported failures”. This makes the conclusion consistent with the corrected protocol description.

9. In the Lock and amendments paragraph, identify the source for H2’s exclusion of replacement: add “(public simulator specification, section 6.1)” after “before the lock”, with a supplementary reference to `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md`.

REASON: Most Text actions are applied correctly, including the conditional theorem, equality condition, threat model, README erratum, and limits on coalition results. The provider parameters and first-best assignment definition match the code, but the appendix has an indexing error and an incorrect universal bid restriction. The main prior-work framing is supported; BOINC describes full initial replication, and CrowdEval specifies initial gold-task screening. [BOINC, section 4.6](https://boinc.berkeley.edu/boinc_papers/hicss_08/hicss_08.pdf), [CrowdEval, section 2](https://www.ifaamas.org/Proceedings/aamas2018/pdfs/p1486.pdf) The listed edits resolve remaining attribution, source, and cross-document inconsistencies without changing the reported results or theorem bound. This was a static review; no files were changed, no paid APIs were called, and `sealed/` was not read.

CONFIDENCE: 0.94
