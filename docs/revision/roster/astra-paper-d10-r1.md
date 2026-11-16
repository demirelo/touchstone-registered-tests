VERDICT: reject

CORRECTIONS:

1. `main.tex:22,39,194`: Qualify the C* crossing by search version. Frozen estimates change sign between p = 0.01 and 0.02; doubled estimates are already negative at 0.01 (−0.004). Replace “reverses … on every market” with “is negative on all six markets at 0.03”: some markets were already negative.

2. `main.tex:22,39,194,204,230,234`: State that B3’s advantage survives **in the pooled estimate** through p = 0.03. At that rate, B3−R3 is negative on three markets under both search versions. Avoid a strictly decreasing claim: the frozen pooled gap first increases from 0.173 to 0.175.

3. `main.tex:22,204,234`: Replace “exists only while” with a statement restricted to the tested rates and pooled estimates. At p = 0.05, doubled searches still favour R3 on fresh0. In the conclusion, replace “verified-history targeting” with “C*”; one comparator under churn cannot support a class-wide conclusion.

4. `main.tex:196`: Label the displayed market-level intervals and “not because the sign varies” as **frozen-search results**. Doubled signs vary on fresh0, and the doubled B3−R3 interval excludes zero: approximately [−0.064, −0.001].

5. `main.tex:198`: The audit values and replacement-switch counts match the records. However, four sampled rates do not establish “gradual, not a threshold.” Say that the measured audit share decreases across those rates. Replace the causal explanation of the different crossings with “audit share alone does not determine gain.” Restrict residual-only auditing to the attacker’s established phase.

6. `main.tex:12,21,162`: Explicitly label the churn subtitle and abstract’s Run A/Run B results exploratory. Their reported D2+H3 values and Run B’s 19 passing cells match the records; neither run includes churn cells. Specify D2+H3 for Run A: doubled X7-SC gives the opposite direction (+0.00282). Replace “lower … by −0.010” with “runner-up minus R3 is −0.010.” Section 10’s amendment timing is correctly disclosed.

7. `main.tex:56,68,160,224`: Use Appendix B for the first-test pointer, `sec:reset` for both reset pointers, and Appendix C for the moved addendum disclosure. The registered content and seven moved floats remain present.

8. `churn_paper.py:119`, `test_churn_paper.py`: The freshness check accepts any existing PDF when its JSON matches. Check the PDF’s content or deterministic digest, and test a replaced PDF. The current figure matches the data.

9. `docs/revision/paper-v2/numbers.tex`: This checkout’s generated macros are stale. The direct gate fails freshness; regeneration in memory passes. All 54 gate tests and five churn-paper tests passed with file operations held in memory and PDF drawing stubbed.

CONFIDENCE: 0.97