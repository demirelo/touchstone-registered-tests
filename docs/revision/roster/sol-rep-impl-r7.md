VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup3/rep_collect.py:307` — L1 remains incomplete. A record with the mismatch status, `round1_gate={}`, and `rounds=[]` removes the primary set and makes resume exit 4 without rerunning. A status string alone proves no measurement. Require a well-formed comparison or well-formed round-1 evidence before declaring a mismatch. A fresh gate without either must exit 6.

2. `docs/revision/followup3/rep_collect.py:153` — `_gate_wellformed` raises `OverflowError` when a comparison difference is `10**400`. In-memory probes confirmed crashes in both collection and resume. Handle numeric conversion failure as an invalid record. Preserve the permitted infinite gain difference.

3. `docs/revision/followup3/rep_collect.py:342`; `test_rep_collect.py:964`; `rep-launcher-notes.md`, ruling 10 — Resume treats every unequal provenance object as a foreign binding. Both `{}` and a provenance with `id=None` cause fatal refusal, although malformed provenance must trigger a rerun. Validate provenance structure and field types before deciding that it names another job or run. L5’s guard currently requires the incorrect refusal for these generated inputs.

4. `docs/revision/followup3/rep_collect.py:206` and `:232`; `test_rep_collect.py:954` — `_round1_ready` does not validate the doubling record’s two change values. Setting doubling `attack_change=None` makes collection mark the cell unscorable **and** declare a global mismatch; resume exits 4 without rerunning. Validate the comparison operands before testing disagreement, while retaining L2’s scan before base-record exclusions. Extend the guard to require the correct mismatch state as well as an unscorable cell.

All 173 tests pass, but the in-memory probes reproduce these failures. L3’s queue correction and L4’s shared normalizer checks are present.

CONFIDENCE: 0.99