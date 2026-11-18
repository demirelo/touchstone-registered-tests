# Triage: external paper-only review of draft 10 by Gemini (2026-11-19)

Review: `docs/revision/roster/gemini-paper-d10-ext.md` (WEIS 3.5/5, 65%; AAMAS 3.0; EC 2.5). Prompt:
`docs/paper/paper-only-review-prompt-d10.md`; PDF `results/v2/submission-anon-d10.pdf` (commit 8316cff).
Each claim was checked against the paper source before a disposition was set. Text fixes are applied when the paper is
finished after the churn replication (the author's decision of 2026-11-18: run first, then finish the paper), so the
abstract and Section 10 are not rewritten twice.

| # | Point | Check against the source | Disposition |
|---|---|---|---|
| 1 | 21 of 72 churn cells flagged; references not regenerated under churn | Correct; disclosed on p. 15 | Continued search is in the replication (new markets). Regenerating reference menus under churn is not in the plan: **author decision** (scope and cost) |
| 2 | Only C* under churn | Correct; disclosed on p. 16 | Covered: the replication runs C-thr(12) under churn at p = 0.03 and 0.05 |
| 3 | Abstract omits that R3's selected attack stops replacing on half the markets; C* and B3 crossings not distinguished at p = 0.03 | Partly correct | Text fix at paper finish |
| 4 | Exploratory Run A clause inside the registered sentence of the abstract; "missing period" after C* | Clause placement correct; the period is in the source (`C$^*$. Without`), an extraction artefact | Text fix at paper finish (clause only) |
| 5a | Table 6 caption does not say its p = 0 interval is uncalibrated, unlike Table 3 | Correct | Text fix |
| 5b | 0.571 (honest replacements, first ten rounds) differs from Table 9's young honest share | Correct: two different statistics, the first undefined in the text | Text fix: define it |
| 5c | Rounding 1.053 vs 1.05; typos "of ther", "90.05(R3)" | Rounding correct; the typos are not in the source (PDF extraction of `the` ligature and $g_{0.05}$) | Harmonise rounding only |
| 6 | Section 9 reference sensitivity is a Mac additive proxy; asks for a Linux re-evaluation with non-replacing references | Correct as described; the paper says it is a proxy | Needs compute: **author decision** (could run on the replication pod) |
| 7 | Three missing citations | All three verified (DOIs 10.1093/restud/rdaa012, 10.1287/isre.1060.0092, 10.1287/isre.2021.0146) | Add at paper finish |
| T | Prop. 1 text says b > 0.22 | Wrong: the source says $b \ge 0.22$ (line 110) | No change |
| P | Presentation: acronyms in Results in brief; FlashProve detail; expectations list; Q1 paragraph length; abstract length | Fair | Edit at paper finish |
