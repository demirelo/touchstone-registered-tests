VERDICT: reject

CORRECTIONS:
1. **Result sites — residual limit:** Change “same kind” to “any kind” and add a regression test for a count/gain swap. An in-memory check accepted exchanging `q4-count` and `q1-d2h3-d`. The checker validates each manifest entry’s kind, but does not bind that kind to its sentence. The final PDF comparison is an acceptable manual check, but the stated limit is too narrow (`docs/revision/paper-v2/numbers_v2.py:188`, `:196`; `docs/revision/paper-v2/outline.md:26`).

2. **Result coverage — omitted regions:** Add the requested source coverage manifest and a regression test for an unmarked integer in an included caption outside the abstract/results sections. After source expansion, `\caption{Replicated on 4 of six markets.}` still returns no error. Full-section enforcement covers only two section keys; the remaining scan checks only numbers with three or more decimal places. Round-3 correction 2 remains incomplete (`docs/revision/paper-v2/numbers_v2.py:23`, `:203`, `:208`).

3. **Result sites — commented text:** Exclude LaTeX comments from site-use counting while preserving region markers. Add a test requiring a site used only in a comment to fail as unused. Commenting out the results sentence containing both registered sites still returns no error, although neither result appears in the PDF (`docs/revision/paper-v2/numbers_v2.py:191`, `:192`, `:207`).

CONFIDENCE: 0.98
