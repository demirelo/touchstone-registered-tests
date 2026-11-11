VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `docs/revision/followup2/guards.py:195`.** Round-4 evidence validation remains incomplete. In-memory probes accepted missing copied inputs, an empty reproduction freeze, unrelated evaluation provenance with a wrong search dependency hash, and unrelated doubling provenance with empty dependencies. The numerical comparisons still passed. Validate supporting records’ provenance, complete dependency sets, freeze contents, and actual copied-input hashes against registered records. Add refusal tests that use the real comparison functions.

2. **Block pod — §5; `docs/revision/followup2/guards.py:115`, `:149`.** The event parser now accepts the launcher’s format, but paid admission accepts an empty attempts file, multiple open attempts, globally unordered events, and an allocation timestamp unrelated to the open event. Require finite, ordered timestamps and exactly one current open attempt. Bind its identity and allocation time to admission. Add refusal tests. Remove §5’s obsolete four-field format and nonexistent `prior_from_attempts` reference.

3. **Before allocation — §§5–6; `results/pods/reset_pod.sh:118`.** Complete and test the actual Run A launcher copy. The supplied template still invokes the reset driver and retrieves reset directories; it does not implement the stated attempts/ledger transfer. Test argument transfer, cumulative spending across relaunches, STOP/deadline handling, Run A retrieval, and verified deletion. The driver now checks STOP before each internal stage; that round-4 correction is present.

4. **None — §§1, 3–4 and remaining driver checks.** The estimand answers sensitivity to one development-selected alternative. Advance expectations, matched base/doubled contrasts, nominal interval limits, and deferrals are appropriate. All 12 specifications, pairings, budgets, configurations, and 108 bank hashes passed. The benchmark reproduces 17.65 core-hours and USD 1.99 billed cost; the proposed USD 3 reservation matches the admission cap.

5. **§2 validation.** Both Run A Mac gates now pass recomputation, with matching inventories and copied inputs. Forty read-only tests passed; 38 tests requiring temporary files, including smoke execution, were not rerun. Retain full-suite and bit-identical pod gates before searches. Run B’s saved gates report passes, but their embedded driver hashes differ from the current driver; its current inventory does not cure those stale bindings. This last issue concerns Run B.

CONFIDENCE: 0.98.