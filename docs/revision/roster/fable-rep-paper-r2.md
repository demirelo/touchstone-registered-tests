# Fable 5.2, review round 2 (rep-paper-r2), as returned to the session on 2026-11-24

VERDICT: accept-with-caveat

CORRECTIONS:
1. main.tex:210 (and caption at 394): "the plan ran diagnostics for continued R3 winners only at p = 0 and 0.05" is wrong; the plan (section 2) asks for R3's allocation without a rate restriction. The limit is in the stamped collector (rep_collect.run_diagnostics). Attribute it to the run code, call it a gap against plan section 2, and name the missing markets (rep2, rep3, rep4).
2. main.tex:21 and 37: "mean changes rest mainly on two markets" lacks the winner-set qualifier while the sentence also cites the frozen winners; true only for the primary winners (frozen 0.05 d: rep4 -0.353, rep3 -0.174). Add "with the primary winners".
3. main.tex:35, 206 (heading), 248, 377 (heading) still say "prospective replication"; round-1 label point partly fixed.
4. replication_paper.py _validate: Sol 6 / Astra 5 partly fixed. Six edited-extract probes with the same analysis hash still pass: altered allocation value; continued stem swapped for another valid stem; dropped primary 0.05 market; altered audit counts with the same verdict; altered draw hash; removed frozen 0.03 audits. Add guards that hold on the committed data: focal_audit_rate equals audited over served; continued set equals the cells whose primary and frozen terms differ (20 = 20); frozen coverage 18/18 and primary gaps only for continued R3 cells at 0.03; compare the draw and manifest hashes with something.
5. (optional) tables/replication_markets.tex: print or disclose the paired-change seed-bootstrap intervals held in the analysis.
6. (optional) tables/replication.tex: the primary q interval at 0.05 prints as [-0.061, 0.000] (upper +0.0005); print four decimals or add a note.

Round-1 status: fixed except the label (3) and the validation (4). Every value in lines 206 to 212 and Tables 10 and 30 to 33 matches the analysis and extract; allocation() is identical to churn_block.audit_allocation; the wrappers leave the collector's decisions unchanged. No contradiction with plan section 8 and no new overclaim beyond correction 2.

CONFIDENCE: 0.86
