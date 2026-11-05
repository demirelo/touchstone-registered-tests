VERDICT: reject

CORRECTIONS:

1. **main.tex:304 — welfare sign error.** B3’s selected W0 attack earns **+0.2536** relative to its truthful reference. Only R3 and C* earn less than their references, approximately −0.0939 each. Restrict the conclusion’s loss statement accordingly.

2. **main.tex:285–288; PDF page 19 — clipped predictions table.** Table 17 extends below the page. Q3-c is truncated; Q3-d through Q4-b and the caption are absent from the visible PDF. Split the table across pages and check the new PDF.

3. **main.tex:247; posthoc_v2.py:82; response-to-review-r4.md, point A — weight rounding changes the claimed bound.** The computed R3 lottery uses probability **0.4195**, with lower bound **0.0000279**. At the printed probability **0.42**, that bound becomes **−0.0000531**. Print the exact weights, including C*’s **0.4845**, and identify the bounds as descriptive normal approximations after weight selection on evaluation seeds.

4. **main.tex:171; response letter, calibration paragraph — specify endpoint denominators.** State **m_Q1 = 8** and **m_Q4 = 36**. The two-market branch tests 24 Q4 endpoints but conservatively retains denominator 36, as design 9.5 requires and coverage.json confirms.

5. **main.tex:213; response letter, heterogeneity paragraph — remove the mechanism claim.** The profit split, audit spending, and served share do not establish that passing and failing markets have the same mechanism. Report the measured differences and leave their cause unresolved.

6. **tables/posthoc_stability.tex — increase precision.** Three decimals hide both changes. Print at least four decimals: **0.0207 → 0.0209** and **0.0243 → 0.0245**.

7. **response-to-review-r4.md — update table references and completion claims.** The Q1 reference-profit row is in **Table 6**, and predictions are in **Table 17**. Revise “every sentence correction is applied” after correcting the conclusion and restoring the complete predictions table in the PDF.

CONFIDENCE: 0.98.