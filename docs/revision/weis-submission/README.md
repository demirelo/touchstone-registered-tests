# WEIS 2027 submission package

Status (checked 2026-11-25 at https://weis2027.econinfosec.org/): no call for papers and no submission site yet.
Tentative dates: submission 21 January 2027, notification 11 March 2027, workshop 16-17 June or 30 June-1 July 2027.

## Files
- `weis2027-anonymous.pdf`: 47 pages, built by `results/pods/paper_pdf_weis.sh --anon` from commit 1663133;
  SHA-256 b135ff85ced6c0ffe1c924ff683ad7153d5e84b6371c4ca655b2be923c57bcd2; `check_anon_pdf.py` passes (text,
  metadata and compressed streams).

## Form fields
- **Title:** Audit the Newest Identities First? Preregistered Simulation Tests of a Verification Rule and Their Limits Under Honest Turnover
- **Authors:** entered in the submission system only (the PDF is anonymous).
- **Abstract (248 words by `wc -w` on the PDF text, as in the PDF):** A buyer of computation can check only a sample of delivered jobs, and a sanctioned provider can return at once under a new identity; under uniform audits with refund-and-ban enforcement, free replacement makes the ban costless, given honest rivals whose play does not depend on the focal identity. We study R3, a rule that audits new identities first and then keeps targeting the newest ones, in two registered simulation tests; the second was locked before six fresh markets were drawn from a Bitcoin block hash. Without honest identity turnover, the registered gain-and-efficiency comparison of R3 with uniform audits (B3) passes on 3 of six markets under the prescribed searches, all passes qualified by search flags, while R3 lowers the attacker’s measured gain relative to B3 on every market; R3 and a verified-history comparator, C*, tested in the second test only, are “equivalent, direction R3 lower” within a pre-set margin (C*minus R3: 0.021). Exploratory follow-ups suggest that R3’s advantage over B3 erodes when honest providers also replace their identities: R3’s audits move to honest newcomers, and the share of the attacker’s jobs it audits falls from 0.366 to 0.042 between churn rates of p = 0.01 and 0.05 per round. A prospective-exploratory replication on six new markets, planned and timestamped before they were drawn, met all 5 of its expectations with its primary search winners (4 with the all-frozen winners); with the primary winners its mean changes rest mainly on two markets, and its market-level intervals mostly include zero.
- **Plain-language summary (if the form asks):** `docs/revision/plain-summary.md` (names no person or repository).
- **Keywords (suggested):** audits; Sybil attacks; whitewashing; reputation; verifiable computation; mechanism design; preregistration; simulation.
- **Artifact for reviewers:** https://anonymous.4open.science/r/audit-newcomers/ (pinned to ef93b88; all 669 files with an identifier
  in that commit scanned clean on 2026-11-25 after four added terms).
- **Prior publication:** the full paper and its records are public (non-anonymous release v2.1, two Zenodo DOIs). WEIS is
  non-archival; if the form asks about public versions, say so without giving the link.
- **AI use:** stated in the PDF ("Use of AI tools"); the author approved it on 2026-11-25.

## When the call opens
1. Read the call: page limit, format, anonymity and AI-use rules, deadline. Change the PDF only if a rule requires it,
   then rerun `results/pods/paper_check.sh` and `paper_pdf_weis.sh --anon`.
2. Re-check the mirror still resolves and still masks the terms.
3. The author creates the submission account, enters the fields above, uploads the PDF, and submits.
