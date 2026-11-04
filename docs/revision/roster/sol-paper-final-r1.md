VERDICT: accept-with-caveat

CORRECTIONS:

1. main.tex:37,282,285 — Correct the statements that the record and release are public. The GitHub repository is private, and its release list is empty. State that publication is planned, or provide a verified public archive link and the exact report commit. H4’s unsealing does not establish public availability.

2. main.tex:285 — Narrow “one-command reproduction of every table.” `reproduce_deviation.py` checks the second-test report files; it does not regenerate the first-test verdict table or the paper’s LaTeX tables. State the supported scope or supply the complete reproduction command.

3. main.tex:114–126,194,199,250 — Fix the table widths. Table 1 extends beyond the PDF’s right edge; Tables 4, 5, and 11 exceed the text width. Also fix the smaller overflow at line 77. Use wrapping columns and check the rebuilt PDF.

4. main.tex:210–211, Table `tab:q4` — Add the prescribed-search qualification for fresh0 and fresh3, whose reference dependencies are flagged. The table currently marks only fresh1 and fresh4. Match line 207 and the addendum, preferably with a caption note that covers all four markets.

5. main.tex:265–266, Table `tab:predictions` — Define the bracketed value pairs. They represent different quantities across predictions and can look like confidence intervals, including reversed intervals. Label their components and round the raw floating-point values.

CONFIDENCE: 0.96.