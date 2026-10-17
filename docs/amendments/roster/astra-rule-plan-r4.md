Round-3 OPEN and NEW points, with duplicates combined:

- **RESOLVED — H3 checks dispatch.** A1 assigns the dispatcher change, preserves D1/D2 matching, rejects missing inputs, and requires one H3 checks record per rule.
- **RESOLVED — L = 20 fixture.** A5 specifies quotas in `{8, 9}` that total 1500 over 180 early rounds.
- **RESOLVED — Complete commands.** A6 supplies the sweep, harness, and `amend.py --check` commands with the required paths.
- **RESOLVED — External-bank resolution.** A6 requires one resolver for all bank-consuming stages, including resumed stages, with a test over separate development and final directories.
- **RESOLVED — F5 bank commitment.** A6 records the bank hash, source-map hash, and embeddings in freeze-protected `experiments/proposed.yaml`; claim verification rejects a different, internally valid bank.

**NEW — MATERIAL: unconditional control rejection blocks final evaluation.** [A1, line 38](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/superpowers/plans/2026-10-17-proposed-rule.md:38) requires every control to find a `development` or `h3` record. However, the [final sweep command](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/lock-runbook.md:102) runs `--stage all --sections heldout` in a separate directory. The current checks loop visits every control. Under A1’s new rule, it will reject this run because those development records are absent. A6’s external bank supplies the bank document, not those records.

**Repair:** Define which controls are required for each selected section. Reject missing inputs for required controls; exclude controls outside the selected scope. Require the separate-directory test to run the exact final `--stage all --sections heldout` path successfully.

Read-only review. No tests or simulations ran. The sealed bundle remains unread.

**VERDICT: reject**  
**CONFIDENCE: 0.95**
