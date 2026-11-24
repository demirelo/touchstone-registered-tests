VERDICT: submit-after-minor

CORRECTIONS:

1. **main.tex:19–40, 163, 189–253 — Shorten and refocus the main text.** The paper has 44 pages, with the appendix starting on page 23. The abstract carries too many results, the Q1 paragraph spans almost two pages, and the conclusion repeats most findings. Put the economic finding first: age targeting limits measured gains when honest identities persist, but honest turnover redirects audits and weakens that advantage. Move the detailed FlashProve discussion, search histories, and repeated sensitivity results to the appendix. Keep the registration labels and essential uncertainty statements beside each claim.

2. **main.tex:62–72, 114 — Complete the behavioral definitions.** “Honest” specifies effort and claims but omits bids. The implementation makes honest opponents bid their delivery cost, \(a_i+b_iq_i^{\max}\). State this explicitly: it affects allocation, payments, and attacker profits. Also explain that the focal truthful reference maximizes mean normalized training profit over its candidate menu; it is not necessarily the opponents’ full-effort policy and can replace identities.

3. **Figure 1; main.tex:22, 38, 213, 249, 253; Table 10 — Make uncertainty visible in the headline result.** Figure 1 shows pooled curves without market variation and omits the new replication. Add a replication panel with individual-market values and market-level intervals. Replace “advantage lasts through” with “the pooled point estimate remains positive at.” At \(p=0.05\), all six new markets have negative primary absolute contrasts, but all three corresponding market-level intervals include zero. Preserve that distinction in the opening and conclusion.

4. **main.tex:181; Table 5 — Compare intervals for the same quantity.** “Its paired-seed interval excludes zero” follows the definition of \(S\), but the subsequent \([-0.036,0.018]\) market interval describes \(G(\mathrm{D2})\), not \(S\). Name both quantities explicitly, or compare the seed and market intervals for \(G(\mathrm{D2})\). The present sentence suggests two uncertainty estimates for one estimand.

5. **main.tex:105; Theorem 1 — Correct the theorem description.** Theorem 1 bounds long-run excess **profit**, not the attacker’s audit rate. Replace “audit rate” accordingly. Consider removing this unused theorem from the submission version: its assumptions are not established for the implemented process.

6. **Figure 1 caption; main.tex:195 — Distinguish gain from earnings.** Negative contrasts establish higher measured excess gain against R3, relative to each rule’s own truthful reference. They do not, by definition, establish higher total attacker profit. Replace “the attack earns more” with “the measured attacker gain is higher.”

7. **Tables 9, 30, 31, 33 — Improve legibility.** Width scaling makes the entries substantially smaller than the surrounding text, especially Table 9. Split wide tables by winner set or statistic. Retain all values, but avoid shrinking an entire matrix to fit one text-width block.

8. **main.tex:14, 132, 256 — Submit the anonymized build.** The supplied PDF still shows the author’s name and identifying H4 hash. The existing anonymizer removes both; its in-memory check passes, and I found no additional explicit identity leak in the bibliography. Verify the final PDF against the double-anonymous requirement. [WEIS submission rules](https://weis2026.econinfosec.org/). Also reconcile “will be released” at lines 38 and 253 with the already-public Availability statement.

TOP-3:
1. Shorten the opening and main results around the economic finding and its limits.
2. Define honest bidding and truthful-reference selection explicitly.
3. Show the prospective replication and market uncertainty in the main figure.

CONFIDENCE: 0.91.