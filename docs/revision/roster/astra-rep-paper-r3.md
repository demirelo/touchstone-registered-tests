VERDICT: reject

CORRECTIONS:

1. **replication_paper.py:110–170; replication_extract.py:138–144 — Partly fixed (Sol 6; Astra 5; Fable 4).** Repeated probes now reject wrong draw/manifest hashes, substituted continuation identities, impossible cthr/F111 identities, missing required markets, negative or excessive audit counts, out-of-range shares, and inconsistent focal rates. However, with the analysis hash unchanged, the **full `check()` still passes** after doubling primary p=0 rep0 counts from `[112797,164572]` to `[225594,329144]`; swapping primary p=0.05 rep0/rep1 young-honest job shares; or swapping their replacement switches. An arbitrary within-range allocation edit also passes `_validate()` and `summary()`, although freshness checking detects changed outputs. Producer-side analysis recomputation does not authenticate these extract fields; `recomputed: true` survives edits. Compare the extract against source-derived records and add rejection tests. The new checks accept the committed data; the 20 continuation identities match the 20 differing cells.

2. **main.tex:206–210; replication*.tex — Fixed (Sol 1–3, 5, 8; Astra 1–2, 4).** Market intervals now explicitly state 95%. Baseline differences, attack/reference terms, efficiencies, support/material counts, expectation verdicts, concentration, the mixed 0.03 comparison, and pooled intervals agree with the JSON. All five tables reproduce. Interval construction matches plan §2.

3. **main.tex:210,394; replication_alloc.tex — Fixed (Sol 4; Astra 3; Fable 1).** The text correctly attributes missing primary 0.03 diagnostics to the run code, identifies rep2/rep3/rep4, and calls this a gap against the plan. Allocation means agree. Replacement counts are primary 6/6, 1/3, 4/6 and frozen 5/6, 3/6, 3/6 across the three rates. The new sentence and column match these counts.

4. **main.tex:21,35,37,206,248,252,377 — Fixed (Sol 7; Astra 6; Fable 2–3).** Concentration statements specify primary winners. Replication labels consistently say “prospective-exploratory.” Earlier-comparator and rate qualifications remain correct. I found no additional substantive contradiction with plan §§3,4,8.

5. **replication_markets.tex; main.tex:382 — Fixed numerically, caption partly fixed (Fable 5).** Per-market and pooled paired-change bootstrap intervals now appear and match the JSON. The unchanged caption does not identify the second-line intervals. State that these are 95% paired seed-bootstrap intervals and that the pooled interval holds markets fixed.

6. **replication.tex — Fixed (Fable 6).** The primary 0.05 absolute q upper bound, 0.0004752422, now prints as 0.0005.

7. **test_replication_extract.py; test_replication_paper.py; paper_check.sh — Verification limit.** Forty-eight read-only tests passed; the file-writing test was excluded. I inspected the updated label guard but did not execute the full gate because it writes files.

CONFIDENCE: 0.97.