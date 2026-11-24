# Touchstone paper: whole-paper submission-readiness review, round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, `~/h4-session.out`, or anything under `results/pods/mac_diag`; `sealed2/h4/` may be read; reasoning effort high; under 700 words)

The paper is the full draft at commit `ef93b88` (public at https://github.com/demirelo/touchstone-registered-tests).
Read the whole paper, not one section. The last whole-paper external review was round 9 or 10 (`docs/paper/external-review-r9.md`,
`docs/paper/response-to-review-r9.md`); since then a prospective-exploratory churn replication was added (end of Section
"Honest identity churn", Table 10, Appendix B tables 30 to 33) and the abstract, contributions, results in brief, limits,
conclusion and Availability paragraph changed. Do not trust any summary, including this one; check the files.

Inputs:
- PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/paper-final-r1.pdf` (44 pages, built from `ef93b88`).
- Source: `docs/revision/paper-v2/main.tex`, tables in `docs/revision/paper-v2/tables/`, values in the JSON inputs listed in
  `docs/revision/paper-v2/sites.json` (paths) and the gate `results/pods/paper_check.sh` (in the main checkout).
- Registered protocol and plans: `experiments/protocol-v2.yaml`, `docs/revision/followup3/replication-plan.md`, the churn plans under `docs/revision/`.
- Venue: WEIS 2027 (double-anonymous; no page limit in the 2026 call). Target readers: security economics.

Check:
1. Claims against evidence across the whole paper: any sentence that says more than its table, plan or interval supports;
   registered versus exploratory labels; causal wording where only description is licensed.
2. Internal consistency: abstract, introduction, results in brief, discussion, limits and conclusion agree with each other
   and with the sections they summarise (numbers, counts, which comparator, which rates, which winner set).
3. Structure and reading load for WEIS: is the main line clear in the first two pages; is anything in the body that belongs
   in the appendix, or the reverse; is the paper too long for its claims.
4. Anything that would block submission: missing definitions, undefined notation, broken references, stale text, a
   leak of the author's identity outside the Availability paragraph (the anonymizer hides that paragraph's links).
5. The three changes you would make first, ranked by how much they would raise the chance of acceptance.

Output exactly:
VERDICT: submit | submit-after-minor | major-revision
CORRECTIONS: numbered, each with main.tex line or table/figure number, ranked by importance.
TOP-3: the three highest-value changes, one line each.
CONFIDENCE: 0 to 1.
