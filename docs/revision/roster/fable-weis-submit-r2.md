# Fable, weis-submit-r2

VERDICT: submit-after-minor (WEIS version only; the full PDF as supplied is not anonymous)

CORRECTIONS:

Round-1 status:
- **Fixed in both:** Sol 3, 4, 5, 6, 7; Astra 2, 4, 5, 6, 7; Fable 8, 11, 12, 14; "the Mac" (`grep -c Mac` gives 0 and 0).
- **Fixed in WEIS, not applicable to full:** Sol 12, 13; Fable 1, 2, 4, 5, 7.
- **Fixed in WEIS only:** anonymity (Sol 1, Astra 8) and length (Sol 2, Astra 1). The full PDF still prints the name, repository and DOIs, and its abstract and contributions are unchanged.
- **Partly fixed:** Fable 3, 6, 9, 10, 13 (items 5 to 9 below).

1. Both, AI statement (WEIS l.240, full l.265): "Two attackers involve language models" omits H2. `docs/custodian.md` l.5 and the Sealing paragraph (WEIS Appendix E) record that a separate AI session wrote and held H2. H2 is the family that failed the original claim. Name it.
2. Both, same lines: "drafted parts of the text" understates the record. All 135 commits to the paper sources carry a Claude co-author trailer, and none lacks one (`git log --format=%(trailers)`, `awk 'NF==1' | wc -l` gives 0). The release history shows this to any reviewer. Write "drafted the text".
3. Both, WEIS l.197, 199, 266, 311; full l.200, 208, 291: the "external review(s)" are model reviews in the record (`docs/paper/external-review-r8.md`, `astra-pro-ext12-triage.md`). The statement does not connect them, so a reader assumes human reviewers. Add one sentence. Also change "set … decision rules" to "decided": the triage of 2026-10-27 shows reviewer-proposed rule changes accepted before the lock (D11, D12, D14).
4. WEIS, Availability l.237: the mirror is pinned to `ef93b88`, and the anonymity depends on its masking list. In that commit, 376 files contain "demirel", 345 contain "/Users/oemer", and 45 contain the public title (`git grep -l … ef93b88 | wc -l`). I did not fetch the mirror. Confirm zero hits there before submission, or the new title gives no protection. Local check passed: `paper-weis` is absent from `ef93b88` and no remote branch contains `799a745`.
5. WEIS PDF: two embedded figure dates remain (`D:20261104210106+02'00'`, found by an in-memory `zlib` scan). `check_anon_pdf.py` reads only `pdftotext` and `pdfinfo`, so the gate cannot see them. `posthoc.json` also remains twice. Appendix F masks the H4 model while the AI statement names its vendor; make them agree.
6. Both, abstract (WEIS l.22, full l.23): "met 5 of its five expectations" remains. WEIS l.234 prints "negative on 6 and 6".
7. Wording:
   - Full l.23: "find that … removes most of R3's measured advantage" is causal for two separately searched winners. Use "suggest" and "disappears", as WEIS l.179 does.
   - WEIS l.38 (iii): "removes" has the same fault.
   - Full l.39: "substitute for each other" is firm; say "in the pooled contrasts".
   - WEIS l.22: "this advantage" follows the equivalence clause; name B3.
   - WEIS l.193: the "more than three times the margin" sentence needs "point estimate".
8. Both, Section 6 (WEIS l.130): "the report review" comes before the report is defined (l.159). `d = 0` at l.161 comes before the definition at l.199. S and G keep two meanings (l.179, l.246).
9. Both: "its author's note" for H4 (WEIS l.130) sits beside "No AI tool is an author". Write "its writer's note".
10. Full: no anonymized build exists, and the abstract is still about 411 words.

No new numerical error found; neither PDF shows "??" (`grep -c` gives 0). Theorem 1 is no longer interrupted. I did not run `paper_check.sh` because it writes files, and I did not read the full paper's appendices line by line.

FORECAST: WEIS version p = 0.20. The base rate is about 0.3, from memory and not verified.
- The evidence is one stylised simulation; the main results are an equivalence label and exploratory erosions whose market intervals mostly include zero.
- The registration record and the prospective replication are rare and credible, and the body now states the economic trade-off early.
- 47 pages and dense labels keep the reading cost high, and heavy disclosed AI authorship with model-only "external" reviews can lower reviewer trust.

Full paper p = 0.03 as supplied, because it is not anonymous; p = 0.10 if anonymized.
- The 411-word abstract and long contributions hide the question.
- The evidence limits are the same.
- It keeps the causal wording in the abstract.

CONFIDENCE: 0.7
