VERDICT: accept-with-caveat

CORRECTIONS:

1. **main.tex:114, Table `tab:families`:** Fix the table width. The PDF clips the rightmost “Where” column at the page edge. Wrap that column. Also fit Tables `tab:q1`, `tab:q1-side`, and `tab:q3-coalitions` within the text width; they extend into the right margin.

2. **main.tex:211, Table `tab:q4`:** Add the reference-derived search qualification to fresh0 and fresh3. The table currently marks only fresh1 and fresh4 as search-flagged. Match line 207 and the addendum, preferably with a caption note identifying all four affected decisions.

3. **main.tex:266, Table `tab:predictions`:** Explain the prediction identifiers and label the components of each numerical pair. The current unlabelled brackets can look like confidence intervals, although several contain two different estimates or statistics. Round the full-precision values consistently. Fix float placement: this results table appears after the bibliography on PDF page 21.

4. **main.tex:285, Availability:** Identify the release URL and exact tag or commit, and state its current publication status. The supplied evidence confirms the H4 files and reproduction wrapper, but does not establish the complete public archive or successful clean reproduction. Name `docs/revision/deviation/reproduce_deviation.py`; its implementation checks the protocol-v2 report, so qualify “every table” unless reproduction also covers the first-test and paper-specific tables.

CONFIDENCE: 0.95.