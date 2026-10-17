Read-only review of [v4](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/superpowers/plans/2026-10-17-proposed-rule.md). No files changed. No tests or simulations ran. The sealed bundle remains unread.

- **RESOLVED — H3 checks dispatch.** A1 assigns the selector change, requires refusal of missing inputs, and adds an integration test for every rule.
- **RESOLVED — L = 20 fixture.** A5 specifies quotas in `{8, 9}` totaling 1500 over 180 early rounds.
- **RESOLVED — Complete commands.** A6 supplies the calibration and tuned-directory arguments, the harness command, and the complete amendment check.
- **RESOLVED — External bank loading.** A6 requires one resolver for all stages, including resumed stages, with separate development and final directories in the test.
- **RESOLVED — F5 bank commitment.** A6 records the bank identity in freeze-committed `experiments/proposed.yaml` and requires rejection of a different, internally valid bank.

**NEW — MATERIAL: checks selection conflicts with final evaluation.** A1, line 38, requires missing control inputs to cause refusal, but assigns controls only to `development` or `h3` records. The current [checks loop](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:376) visits every control. The [final command](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/lock-runbook.md:102) runs `--stage all --sections heldout`; its directory contains neither source section. A6 adds bank loading but does not resolve this selection conflict. Final evaluation can therefore stop at `checks`.

Repair: define which controls apply to each selected section and evaluation namespace. Refuse missing inputs for those controls. Add an end-to-end test of the final `heldout` sequence through `checks`, using the external bank.

**VERDICT: reject**  
**CONFIDENCE: 0.93**
