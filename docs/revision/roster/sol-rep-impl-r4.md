VERDICT: reject

CORRECTIONS:
1. `docs/revision/followup3/rep_collect.py:469–477`; `rep-launcher-notes.md`, ruling 8 — Check continued-winner audit counts independently of frozen diagnostics. The outer `fa is not None` condition discards valid continued diagnostics when frozen diagnostics fail their binding check. An in-memory six-market test had valid base records, a passing gate, six continued winners and six valid continued-diagnostics records. Removing only the frozen diagnostics binding changed primary expectation 5 from “met” to “not scorable.” Require frozen audit counts only when the primary cell keeps the frozen winner. Add a regression test for this case.

CONFIDENCE: 0.97.