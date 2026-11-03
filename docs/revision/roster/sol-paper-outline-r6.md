VERDICT: reject

CORRECTIONS:
1. **Section coverage:** Keep a pending section label across blank lines. Report a missing label before processing another heading or reaching EOF. An in-memory `check()` probe accepts an unlabelled `\section{Results}` followed by a blank line. The scanner clears `pending` on that blank line, and the title-derived key satisfies the required-section check. Round-5 S1 remains incomplete (`docs/revision/paper-v2/numbers_v2.py:204`, `:255`).
2. **Caption and figure-note coverage:** Allow whitespace between `\caption` and its argument. Add the requested source coverage manifest for evaluation-2 captions and figure notes, and require those locations inside result regions. Add regression tests. An in-memory `check()` probe accepts `\caption` followed by a newline and `{Replicated on 4 of six markets.}` outside a result region. The matcher requires an adjacent opening brace. This leaves a direct transcription-check gap from round-5 S2/A1; the final PDF read remains the only check for this case (`docs/revision/paper-v2/numbers_v2.py:238`, `:256`; `docs/revision/paper-v2/outline.md:41`).

CONFIDENCE: 0.99
