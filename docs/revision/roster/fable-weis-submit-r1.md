# Fable, weis-submit-r1 (recovered from the session transcript, 2026-11-25)

VERDICT: submit-after-minor (WEIS version; the full paper is not a submission candidate for this venue).

CORRECTIONS:

Status of the earlier items: Sol 3, 4, 5, 7; Astra 2, 4, 5, 6, 7; Fable 3 to 9 and 11 are fixed in both versions. Sol 6 and Astra 3 are fixed by Figure 2 and the landscape tables; Figure 1 still shows pooled curves only. Sol 1, Astra 8 and Fable 1 are fixed in the WEIS PDF only; the full PDF still prints the author, repository, DOIs and block heights (`pdftotext`, `grep`). Sol 2 and Astra 1 are partly fixed in WEIS and not fixed in full (abstract 411 words against 215, `awk | wc -w`). Open items follow.

1. WEIS, Availability l.237 and l.109, 127, 159, 312, 432: the text cites the supplement, the addendum and the audit file, but no anonymous mirror exists (Fable 2, not fixed). The public release also contains "the paper sources", so a search for the title finds the author. This blocks submission.
2. WEIS, l.16, 135, 406, 439: "November 2026", "October 2026" (four places, including the Appendix E title) and "12 November 2026" remain, while l.407 masks the day. Mask them all.
3. WEIS, l.130, 237, 439: repository paths (`sealed2/h4/`, `docs/revision/...`) and "gpt-6.1-sol" (l.437) are searchable in the public repository. The figure metadata carries two time zones (in-memory `zlib` scan of the PDF; no name, no local path, no repository URI found).
4. WEIS, l.195: the body keeps only a pointer without numbers for audit allocation. The abstract (l.21) and conclusion (l.234) give 0.366 to 0.042, which only Appendix C supports. Sol 2 asked for this evidence in the body. Restore one sentence with the numbers and the doubled value 0.505.
5. WEIS, l.234: "that advantage is lost at the tested churn rates" says more than Table 6 permits; B3 minus R3 is 0.175, 0.119 and 0.068 at 0.01 to 0.03. Appendix C also says B3 minus R3 is negative on 3 of six markets at 0.03; the body omits this.
6. WEIS, l.21: "the advantage erodes" has no antecedent; the abstract states no advantage before it. "Show" is too strong for exploratory follow-ups.
7. WEIS, l.358: Appendix B starts with "Search uncertainty matters at this level" and "this comparison"; the verbatim move removed their antecedents.
8. Both, WEIS l.179 and l.351, full l.182 and l.376: the exploratory identity-replacement details sit in the appendix "Further registered results". Rename the appendix or give them their own section.
9. Both, WEIS l.351, full l.376: "The Mac reproduces" remains (Fable 12, partly fixed). "The report" is still undefined at first use (l.38 and l.39).
10. Both, Section 10 (WEIS l.205): the prose uses d, q and u before the Table 7 caption defines them. Fable 13 is not fixed: d, q, p, K, A, H, S, G and I still carry two meanings.
11. Both, Table 35: it still interrupts Theorem 1 (Fable 15). In WEIS, Table 25 and Figure 5 (Q4) interrupt an Appendix C paragraph.
12. Both, WEIS l.168, full l.171: the Q4 heading says "six new markets", the paper's term for rep0 to rep5; Q4 uses the fresh markets (Fable 10, partly fixed).
13. Both, l.22 and l.23: "met 5 of its 5 expectations" (Fable 14, partly fixed). The calibration caveat still appears twice in Section 7 and again in Section 8 and Appendix F.
14. Both, WEIS l.437: an AI model wrote H4 and "sessions" held H2, but the paper has no statement on AI use. Add one, and check the venue rule.
15. Full: the contributions and the 411-word abstract are unchanged in length. Produce an anonymized full build before any submission of it.

Numbers checked: the Section 10 and Table 7 replication values, both sets of five expectation verdicts, and R3's lowest efficiency 0.929 agree with `docs/revision/followup3/replication-analysis.json` (in-memory Python lookup). Neither PDF shows "??" (`grep -c`). The recorded spend sums to 26.45 USD for the replication.

Not checked: I did not run `paper_check.sh`, did not read the full paper line by line, and did not verify the WEIS anonymity or AI-use rules.

FORECAST: WEIS version p = 0.16. Reasons: (1) the main results are an equivalence finding and exploratory erosions with intervals that mostly include zero, in one stylised simulation without field data; (2) the registration discipline and the prospective replication are rare and credible; (3) 46 pages and dense labels (D2+H3, X7-SC, F111) keep the reading cost high, and the economic insight arrives late.
Full paper p = 0.08. Reasons: (1) the 411-word abstract and the two-page Q1 paragraph hide the question; (2) the same evidence limits apply; (3) no anonymized build exists.

CONFIDENCE: 0.7
