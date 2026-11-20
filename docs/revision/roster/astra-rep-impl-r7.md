VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup3/rep_collect.py:307` — L1 remains incomplete. `_mismatch({"status": "stopped: round 1 differs"})` returns `True` without a comparison or measured values. The status bypasses validation, stops resume, and removes the primary set. Require well-formed measurement evidence before declaring a mismatch.

2. `docs/revision/followup3/rep_collect.py:199` — L1/L2 misclassify malformed doubling values. Starting from matching records, setting doubling’s `attack_change=None` makes `_mismatch` return `True`. `_round1_ready` validates the continuation’s changes but omits the doubling’s changes. Validate both sides before comparison. Keep the check before base-record exclusions.

3. `docs/revision/followup3/rep_collect.py:153` — The new comparison validator repeats the oversized-number failure. Setting `max_gain_abs=10**400` raises `OverflowError` in `math.isnan`. This exception escapes `_mismatch`, collection, and resume. Treat oversized integers as invalid while preserving the allowed infinite gain difference.

4. `docs/revision/followup3/rep_collect.py:342` — L5 and ruling 10 require malformed provenance to trigger a rerun. Instead, `{}`, `{"id": None}`, and `{"id": []}` all trigger the foreign-record refusal. A dictionary type check does not establish well-formed provenance. Validate its required fields before deciding whether it names another job or run.

5. `docs/revision/followup3/test_rep_collect.py:954`, `:964`, `:971`, `:986`; `rep-launcher-notes.md`, ruling 10; `rep-impl-r6-response.md`, L1/L5 — The guard still permits incorrect outcomes. Doubling mutations require only an unscorable cell, so an additional false global mismatch passes. Provenance expectations repeat the faulty dictionary check. Resume accepts any exit except 4 after a rerun; queue mutations require only no exception. Assert each prescribed outcome, add the probes above, and correct completion claims. All 173 tests passed; the launcher and harness hashes match the cited log.

CONFIDENCE: 0.99