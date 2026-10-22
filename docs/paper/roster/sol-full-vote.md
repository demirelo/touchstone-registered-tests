VERDICT: reject

CORRECTIONS:

1. **Abstract and §1, “The rule”:** The stronger condition added to Corollary 1 has not reached these summaries. Replace their age-independence claims with: “For B2 and B3, immediate free replacement removes the ban’s continuation cost because replacement preserves the distribution of all payoff-relevant future states up to identity relabelling.” Age-independent rules can still use history-based reputation that replacement destroys. In §8, qualify the opening claim with “Under the conditions of Corollary 1.” This repairs the remaining material overclaim.

2. **§3, “Attackers and the benchmark”:** H1 is still listed among “parametrised families” and included by the subsequent general search description. Replace the opening with “The parametrised families are D1, D2, D2+H3, and H2; H1 is a separate language-model procedure.” Introduce the CMA-ES and extended reference-candidate descriptions with “For the parametrised families”. Retain H1’s separate five-episode procedure and three reference candidates. Evidence: design specification §§5.2–5.4 and `docs/final-evaluation-2026-10-20/README.md`.

REASON: The headline numbers, robustness results, corrected baseline rules, and protocol disclosures agree with the named evidence. The local identity and renewal statements now contain the requested assumptions, and the added [renewal-reward source](https://arxiv.org/pdf/1404.5601) supports the cycle formula under finite-mean and integrability conditions. However, the summary still gives an insufficient condition for eliminating continuation loss, and the methods paragraph still gives conflicting descriptions of H1. These repairs preserve the empirical findings and the corrected conditional theory. No files were changed, no paid APIs were called, and `sealed/` was not read.

CONFIDENCE: 0.94
