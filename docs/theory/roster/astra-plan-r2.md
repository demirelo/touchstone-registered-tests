VERDICT: accept-with-caveat

REPAIRS:

1. **Use one parameter-transfer field.** Global Constraints still require `transfer: true`, while Task 3 correctly uses `param_transfer: true` because bank records already use `transfer` for a diagnostic dictionary. Change the global requirement to `param_transfer: true` and use that field in every stage and report.

2. **Make the renewal gate explicit.** Task 2 requires all assumptions to hold, but its list omits stationary independent cycles, constant conditional established reward and hazard, and finite expected cycle rewards and duration. Include these checks explicitly. A fixed action alone does not establish them when quota, identity priority, or opponent availability changes. Require `applicable: false` when these conditions are unsupported.

3. **Restore the reference-projection test from repair 4.** Extend the D2 embedding fixture to verify that both embeddings enter the compatible bank, their projected candidates reach reference selection in the registered order, and their source and definition hashes enter bank provenance. The current test list specifies the bank winner but does not explicitly test propagation to reference candidates.

REASON: All eight repair areas are present, including independently searched X6 schedules, finite-horizon accounting, quota reconstruction, compatible embeddings, validated parameter transfer, commit-specific records, complete provenance propagation, and stronger acceptance tests. The proposed instrumentation and transfer interfaces match the inspected source code. The 292 search cells and 72 diagnostic configurations match the accepted design. The remaining items are specification clarifications and one missing explicit test; I found no new material design failure. This acceptance covers the plan only; I changed no files, made no paid API calls, and did not read `sealed/`.

CONFIDENCE: 0.94
