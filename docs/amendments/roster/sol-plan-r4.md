- **RESOLVED — Smoke selection.** Task 2 specifies `sorted(universe)[:6]` for smoke runs and ranked `select_cells` for registered runs. This matches the base script.
- **RESOLVED — Registration checks.** Task 4 refuses draft confirmatory evaluation, reports draft status without reading the extension report in `--verify-only`, and verifies registered reports on every non-synthetic invocation. It adds the null-registration CLI test.
- **RESOLVED — Shared fixtures.** Task 2 specifies session-scoped `cal_path_session`, uses `registered_inputs` consistently, and includes `tests/conftest.py` in its file and commit lists.

**NEW objections:** None.

Read-only review. No files changed. No tests run.

**VERDICT: accept**  
**CONFIDENCE: 0.97**
