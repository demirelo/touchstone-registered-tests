# Touchstone: two versions for submission, review round 1 (read-only; no paid APIs; do not read, list or walk `sealed/`, `~/touchstone-h4`, `~/h4-session.out`, or anything under `results/pods/mac_diag`; `sealed2/h4/` may be read; reasoning effort high; under 700 words)

The whole-paper review (`docs/revision/roster/{sol,astra}-paper-submit-r1.md`; a third reviewer's report is summarised in the
commit messages after `650f069`) asked for fixes and a shorter WEIS version. There are now two versions at commit `4f4890e`:
- Full paper: `docs/revision/paper-v2/main.tex`; PDF `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf-full-r2/main.pdf` (47 pages).
- WEIS version: `docs/revision/paper-weis/main.tex` (with `sites.json`, `dropped.json`, `test_weis.py`), built anonymized by
  `results/pods/paper_pdf_weis.sh --anon` (main checkout); PDF `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf-weis-r2/main.pdf` (46 pages, body to page 18).
  The WEIS body moves text verbatim to appendices; it adds a 208-word abstract, a shorter conclusion, pointer sentences
  without numbers, and a replication figure (also in the full paper).
- Diff since the whole-paper review: `git diff 5af1d59 4f4890e -- docs/revision/`. Gate: `results/pods/paper_check.sh` (checks both versions).
- Venue: WEIS 2027 (double-anonymous; no page limit; non-archival). The anonymous artifact mirror link is not yet in the
  WEIS copy; its Availability paragraph shows "[withheld for review]".

Check:
1. Each whole-paper correction (Sol 1-7, Astra 1-8 in the two report files): fixed, partly fixed, or not fixed, in each version.
2. The WEIS version reads as a complete paper: is anything now missing from its body that a WEIS reviewer needs to judge
   the claims (definitions, the decision rules, the uncertainty statements); do the pointer sentences and the new
   abstract and conclusion claim only what the moved text and tables support?
3. Anonymity of the WEIS PDF: any identifying or searchable string left (names, links, block heights, tags, dates, file names).
4. New errors in either version.
5. Your independent forecast: the probability that WEIS 2027 accepts (a) the WEIS version and (b) the full paper, each
   with the two or three reasons that move it most. Do not anchor on any earlier forecast.

Output exactly:
VERDICT: submit | submit-after-minor | major-revision
CORRECTIONS: numbered, each naming the version (full, WEIS, both) and the main.tex line or table/figure.
FORECAST: WEIS version p = x.xx (reasons); full paper p = x.xx (reasons).
CONFIDENCE: 0 to 1.
