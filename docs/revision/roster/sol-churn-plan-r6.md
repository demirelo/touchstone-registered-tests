VERDICT: accept

CORRECTIONS:
1. none — §7; `docs/revision/churn/churn_v2.py:371–392`. Saved measurements require version 2, explicit `"done"` status for every measured task, and coverage of every current evaluation rule. Draft-4 records cannot pass.
2. none — §§3,7; `docs/revision/churn/churn_v2.py:484–486`. Evaluation and doubling dispatch every job through `_run_one`. Only tasks measured in the current command reduce the remaining-work estimate.
3. none — §7; `docs/revision/churn/churn_v2.py:433–495`. Worker limits persist across commands. Diagnostics require matching memory evidence. Admission runs again after preflight selects the worker count.
4. none — §§2–7. No additional pod blocker found within scope. Eleven read-only, in-memory regression cases passed, including all four round-5 cases. These checks used the source functions with memory-backed file operations; the full 32-test suite was not rerun. Launcher review remains excluded.

CONFIDENCE: 0.95.