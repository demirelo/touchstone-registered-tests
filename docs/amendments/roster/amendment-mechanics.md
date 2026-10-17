# Amendment mechanics (lead's draft for the consensus round)

Constraint: `claim` is inside `settings_hash`; every tuned file, sweep record, coverage cell, and the coverage report carry that hash and the tooling refuses a mismatch. So the amendment never edits `experiments/locked.yaml`. The original predicate stays as locked and its verdict is reported.

Proposal:
1. New file `experiments/amendment-2026-10-17.yaml` (outside the hash): the H3 comparative clause (statistic, level 98.75%, threshold 0.10, cells, positions, paired per seed, bound method per the coverage validation), the H3 absolute clause (eff >= 0.90, gain <= 0.30 at beta 0.05), the negative-loss decision (C5), the reason, and the pointer to the roster memos.
2. `sim/claimcheck.py` and `scripts/check_claim.py` gain a second predicate that reads the amendment file and reports both verdicts (original and amended) side by side; TDD; reviewed.
3. Coverage validation of the new endpoint on the registered cells (C2), reported in `experiments/coverage_report_amendment.json`; the amended clause is confirmatory only if admitted, else exploratory (same rule as the original study).
4. Commit, signed tag `lock-2026-10-17-amendment-1`, OpenTimestamps proof, amendment note under docs/, the roster memos under docs/amendments/. `verify_lock` of the original tag still passes (docs/ is allow-listed; the code changes make the amendment a second lock point: the paper names both tags).
5. Only then: proposed.py, tuning, freeze tag, unseal.
Open question for the roster: must the amendment code changes be reflected in a new whole-tree lock tag that the freeze is verified against (yes, I think: `--verify-lock` takes the amendment tag; the original tag's verification is reported once more at the end).
