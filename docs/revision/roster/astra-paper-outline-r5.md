VERDICT: reject

CORRECTIONS:
1. **Result coverage (S2/A2):** Add the requested source coverage manifest and require evaluation-2 captions and figure notes to lie inside result regions. Check complete caption arguments across line breaks. An in-memory check accepted an included `\caption{\nReplicated on 4 of six markets.\n}` outside the results section. The current check examines only lines containing `\caption` (`docs/revision/paper-v2/numbers_v2.py:215`). The single-line regression does not cover this case (`docs/revision/paper-v2/test_numbers.py:224`).
2. **Section coverage:** Require stable labels for every section subject to the number rule, or map the permitted titles to those keys. An in-memory check accepted an unmarked count under `\section{Introduction}`: the scanner produces `introduction`, but `NOBARE` contains `intro`. Thus, the introduction guarantee is not enforced (`docs/revision/paper-v2/numbers_v2.py:24`, `:183`; `docs/revision/paper-v2/outline.md:26`).
3. **Commented sites (A3):** Remove LaTeX comments before expanding includes, preserve region markers, and handle comments after `\\` correctly. Add regressions for both cases. In-memory checks accepted all registered sites when they appeared only after `\\%`, or in a file referenced by a commented-out `\input`. These sites do not appear in the PDF. The comment expression treats any preceding backslash as an escape, and source expansion runs before comment removal (`docs/revision/paper-v2/numbers_v2.py:26`, `:132`, `:178`).

CONFIDENCE: 0.99
