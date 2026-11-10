VERDICT: reject

CORRECTIONS:

1. **Plan §2; convergence_v2.py:97.** Define this as a capped search-extension sensitivity. Later rounds add R restarts to 2R or 3R; they do not double the accumulated budget. One small increment does not establish convergence. Either implement repeated doubling and revise the cost, or retain this design and limit the claims. State explicitly that unflagged cells, frozen banks, and X7’s original D2+H3 incumbents remain unchanged.

2. **Plan §5; convergence_v2.py:169.** Make reproduction a gate. The driver records disagreement only after all rounds for that cell finish, then continues. Before the main run, require a saved comparison with the frozen doubling stage, including held-out seeds, knobs, gains, finite values, and both changes. Add coverage for headline X7 and fresh D2+H3. The smoke test bypasses pairing and cannot establish full-budget reproduction.

3. **convergence_v2.py:171.** Validate saved results before reuse. File existence alone currently skips a cell. Bind each result to input hashes, job provenance, smoke status, stopping settings, and driver version; reject mismatches. Pin the locked search settings as well: the current code check covers the runner and simulator, while reference pairing omits the search budget.

4. **convergence_v2.py:181; reset_followup_v2.py:119,261.** Write a convergence-specific inventory. The reused helper records the reset driver’s hash and reset experiment’s deviations. Record hashes for the convergence driver, shared analysis, imported helpers, plan, and report, with the actual deviations and run arguments.

5. **Plan §§3–4; common.py:33.** Specify whether per-market intervals are required; the implementation returns per-market means and only a pooled interval. Label intervals nominal, conditional on the six markets and selected policies, without search-error or calibrated-coverage claims. Specify headline Q2/Q3 contrasts or explicitly defer them. The stated absence of directional expectations and coalition deferral are acceptable.

6. **Plan §§6–7.** Set an explicit dollar cap, ledger allocation, and stop rule covering failed attempts and idle time before pod creation. The benchmark arithmetic supports the $1.82 estimate; it is not a spending cap. Verification passed for all 14 jobs’ pairing/configuration/code checks and 111 input hashes. Four read-only unit checks passed; I did not rerun the full suite.

CONFIDENCE: 0.95.