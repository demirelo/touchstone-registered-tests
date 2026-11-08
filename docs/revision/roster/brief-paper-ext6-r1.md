# Paper revision after external review round 6: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

An external referee reviewed the round-6 package (AAMAS 2/5, WEIS 4/5 up from 3, EC 1/5). Their review is `docs/paper/external-review-r6.md`. Commit 843c879 (diff against 1403722) applies it to `docs/revision/paper-v2/main.tex` (PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf12/main.pdf`, 26 pages). The response letter is `docs/paper/response-to-review-r6.md`.

Changed code (tests beside each): `docs/revision/posthoc/posthoc_v2.py` (`feasible_mixture`, the training-feasible row in Table 11, `train_rows` -> `lottery_train.csv`, the W1/W0 seed-order check); `docs/revision/paper-v2/numbers_v2.py` (p kind accepts the audit's calibrated and Holm-adjusted fields); `tables_v2.py` (side-table headers); `sites.json` (new sites).

Inputs: `/Users/oemer.demirel/Projects/touchstone/results/v2/report/report.json`, records in `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all/` (search archives in `search/`, references in `reference/`), `docs/revision/posthoc/{posthoc.json,lottery_seeds.csv,lottery_train.csv}`, `docs/revision/audit/audit.json`, design section 9 (`docs/revision/revision-program-design.md`), `docs/revision/predictions-v2.md`. The paper gate (`results/pods/paper_check.sh`) passes.

Check: (1) the C* passage in section 9 and the new training-feasible row of Table 11: are the values right (weight 0.4765, training 0.0000474, evaluation 0.000931, bound 0.000699, efficiency 0.9224), is the selection of that weight described honestly (it was added after the review, on the same evaluation records), and does any sentence still claim H4 is needed? (2) the Q4-b disclosure in Predictions and the Availability paragraph are true and match the referee's request; (3) introduction and conclusion name the W1 comparator and claim no population counterexample; (4) the referee's small-label corrections are applied, and the new side-table headers match the fields (`sim/diagnostic_v2.py`); (5) `lottery_train.csv` lets a reader rebuild the training component means, and `train_rows` reads the right archive entries and reference; (6) the new contributions paragraph is true to the results; (7) every correction the letter reports is also stated in the paper, and the letter is truthful about what was not done; (8) new errors, including in the PDF.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
