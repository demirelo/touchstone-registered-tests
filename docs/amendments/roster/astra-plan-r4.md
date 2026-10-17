- **RESOLVED — Smoke selection.** Task 2 specifies `sorted(universe)[:6]` for smoke runs, consistent with the base script, and ranked `select_cells` for registered runs.
- **RESOLVED — Extension-report verification.** Task 4 refuses draft confirmatory evaluation, permits draft verification without reading the extension report, verifies registered reports on every non-synthetic invocation, and adds null-registration CLI tests.
- **RESOLVED — Shared fixtures.** Task 2 defines session-scoped `cal_path_session` in `tests/conftest.py`, uses `registered_inputs` consistently, and includes conftest in its file and commit lists.

**NEW objections:** None.

Read-only review of v4, both round-3 reviews, and related source code. Tests were not run; this verdict covers the plan.

**VERDICT: accept**  
**CONFIDENCE: 0.97**
