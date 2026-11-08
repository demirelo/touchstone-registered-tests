# External review, round 7 (condensed record)

Scores unchanged: AAMAS main track 2/5, WEIS 2027 4/5, EC 1/5 (confidence 4/5 each). All 19 package files read; 12 are
byte-identical to round 6. Round-6 problems 1 to 5 and changes 1 to 3 resolved; change 4 partly (venue cut not done);
change 5 not done (optional for WEIS). The reviewer recomputed the 0.4765 row from `lottery_train.csv` (the training
constraint binds: at 0.4770 training gain is -0.000042) and tested `score_v2.py`'s Q4-b branch on a separating case
(raw 0.8 and 0.5 calibrate to a tie and fail).

Remaining problems:
1. (Fix before submission.) The scorer credits Q3-a, Q3-b, Q3-d from searches the report flags `incomplete True`, while
   the hashed rubric makes an "incomplete (design 6.5)" target not assessed. Directly affected: 6 of 14 Q3-a pairs, Q3-b's
   X7-SC input, 7 of 10 Q3-d cells. Under that reading: 7 fulfilled, 8 failed, 3 not assessed. Keep the original output,
   add the sensitivity, footnote the three rows, keep 0.0200 visible; a per-target eligibility map is preferable.
2. Contributions (i) and (iii) need their scope (replacement sentences given).
3. Conclusion: 0.932 and 0.921 are the H4 mixtures; label them and add the public values 0.945 and 0.922.

Remaining changes: (1) eligibility map and sensitivity, $0; (2) text scope edits; (3) WEIS version around the economic
result; (4) release manifest (tag, original report, paper archive; scorer, tests, eligibility map, both CSVs);
(5) optional cross-play comparison for AAMAS. No new simulation warranted. Forecast: WEIS 65 percent, 70 after the edits.
WEIS 2027 tentative submission date 21 January 2027 (https://weis2027.econinfosec.org/).
