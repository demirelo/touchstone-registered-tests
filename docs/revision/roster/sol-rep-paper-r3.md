VERDICT: reject

CORRECTIONS:

1. **main.tex:206,208 — Sol 1,5; Astra 1,4: fixed.** Baseline differences, support counts, material-companion counts, frozen expectation verdicts, the 0.5 forecast, and the audit denominator agree with the JSON. The failed expectation receives no causal explanation.

2. **main.tex:206,208,237; replication*.tex — Sol 2,3,8; Astra 2: fixed.** Market intervals now explicitly state 95%. Profit terms, efficiency, absolute contrasts, paired changes, and interval methods agree with the analysis and plan §2. Rep0 and rep1 contribute approximately 72–88% of the primary mean changes. All five tables and the summary pass the freshness check.

3. **main.tex:210,394; replication_alloc.tex — Sol 4; Astra 3; Fable 1: fixed.** The text attributes missing primary allocation diagnostics at 0.03 to the run code, identifies rep2–rep4, and states the gap against the plan. Replacement counts match the extract: primary 4/6 at 0.05 (rep1, rep3–rep5), frozen 3/6 (rep1, rep4, rep5).

4. **main.tex:21,35,37,206,248,252,377 — Sol 7; Astra 6; Fable 2,3: fixed.** Concentration claims specify primary winners. Replication labels consistently say “prospective-exploratory.” Comparator scope and the two nonzero rates are correctly qualified.

5. **replication_paper.py:110–170; replication_extract.py — Sol 6; Astra 5; Fable 4: partly fixed.** Hash changes, substituted continuation identities, missing required cells, impossible counts, and inconsistent focal rates now fail. Extraction recomputes the analysis before writing. However, with the unchanged analysis hash, `_validate` and `summary` still accept a primary 0.05 rep0 young-honest job share changed to 0.5, a flipped replacement switch, or altered audit counts with a matching rate. More decisively, doubling both rep0 audit counts, or swapping rep0/rep1 replacement switches, also passes the **full freshness check unchanged**. Validate the complete extract against accepted source records; `recomputed: true` does not establish that correspondence. No new check rejects the committed data; the continued-cell and differing-term sets both contain 20 cells.

6. **replication_markets.tex; main.tex:382 — Fable 5: fixed numerically; caption needs correction.** Paired-change seed-bootstrap intervals now match the JSON. The caption remains stale: identify the second lines as 95% paired seed-bootstrap intervals and the Mean interval as pooled over the six fixed markets.

7. **replication.tex — Fable 6: fixed.** The primary absolute q interval at 0.05 now prints its positive upper bound as 0.0005.

8. **results/pods/paper_check.sh — Verification gap.** This checkout lacks the gate script. The 65 read-only tests passed; the temporary-file test was excluded. No additional substantive overclaim or plan contradiction was found.

CONFIDENCE: 0.97.