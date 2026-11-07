# Paper revision after external review round 5: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

An external referee reviewed the round-5 package (verdict unchanged: AAMAS 2/5, WEIS 3/5, EC 1/5). Their review is `docs/paper/external-review-r5.md`. The author asked to apply the changes. Commits e7805b8..b34200f (diff against fc5d672) revise `docs/revision/paper-v2/main.tex` (copied to `paper/`; PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf9/main.pdf`, 25 pages). The response letter is `docs/paper/response-to-review-r5.md`.

New and changed code (tests beside each):
- `docs/revision/audit/audit_v2.py` -> `audit.json`, `paper-v2/tables/audit_*.tex`: raw, calibrated, and Holm-adjusted p-values recomputed from the records and checked against the report; Q4 per market under the report and the registered configurations (records in `/Users/oemer.demirel/Projects/touchstone/results/v2/deviation/stability/`); extreme-interval scan and studentization diagnostic.
- `docs/revision/paper-v2/tables_v2.py` (Q1 and Q4 p-value columns and labels), `score_v2.py` (Q4-b on calibrated p-values).
- `docs/revision/posthoc/posthoc_v2.py` (lottery sensitivity, labels, both companions, `lottery_seeds.csv`).
- `docs/revision/report-addendum/addendum_v2.py` (0.0074).

Inputs: `/Users/oemer.demirel/Projects/touchstone/results/v2/report/{report.json,report.md,addendum.md}`, records in `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all/`, frozen code `scripts/report_v2.py`, `sim/decisions_v2.py`, `sim/intervals.py`, design section 9 (`docs/revision/revision-program-design.md`), `docs/revision/predictions-v2.md`. The paper gate (`results/pods/paper_check.sh`: number check, paper tests) passes.

Check: (1) the referee's finding 1: is the trace right that the report stores raw Q4 component p-values and the calibrated Q1 value, so the frozen decisions follow the registered rule and only the labels were wrong? Is the audit's recomputation correct, and are the new column labels and captions true? Is Q4-b now scored as registered? (2) every lottery sentence (abstract, introduction, section 9, discussion, conclusion, Tables 11 and 12) is calibrated as an exploratory estimate on the selecting evaluation records, with no claim of population profitability; the D2+H3 companion numbers and the training-feasibility statement are right; (3) the fresh1 extreme-interval explanation matches the frozen code and the data; (4) the referee's findings 4 to 8 are applied; (5) the letter describes the changes truthfully, including what was not done; (6) new errors, including in the PDF.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
