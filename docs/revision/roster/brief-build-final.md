# Final whole-branch review of the revision build (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,500 words)

Branch `revision-v2` in the worktree `.worktrees/revision` (you are run with that worktree as the root), range `c2f2a08..HEAD` (`git diff c2f2a08...HEAD`). Plan (accepted by both seats, round 3): `docs/superpowers/plans/2026-10-22-revision-build.md`; design (accepted, round 6): `docs/superpowers/specs/2026-10-22-revision-program-design.md`. The executor's rulings and one deviation are in `.superpowers/sdd/2026-10-22-revision-build/rulings.txt`; the plan's Review Focus (input classes the tests do not exercise) is in `.superpowers/sdd/2026-10-22-revision-build/review-focus.txt` — check each one deliberately.

New code: `sim/mechanisms/pacing.py`, `factorial.py`, `credibility.py`, `sim/rules_v2.py`, `sim/policies/x7.py`, `sim/policies/v2.py`, `sim/instances.py`, `scripts/block_draw.py`, additions to `sim/intervals.py`, `sim/decisions_v2.py`, `sim/objectives_v2.py`, `sim/manifest_v2.py`, `experiments/revision-v2-manifest.yaml`, `sim/h4_loader.py`, `sim/records_v2.py`, `sim/families_v2.py`, `scripts/revision_v2.py`, `scripts/tune_v2.py`, `sim/calibration_v2.py`, `scripts/coverage_v2.py`, `scripts/benchmark_v2.py`, and their tests.

Check with file:line evidence: (1) each implementation matches the design and the plan (rules and oracles, credibility updates, X7-SC transition order and embedding, injected constants, generator and streams, block reader binding, intervals and decision rules, welfare and coalition objectives, manifest counts and cuts, reference menu, dependency and freeze order, acceptance, doubling, salt, H4 loader, tuning objective, coverage selection and validation, cost table); (2) correctness bugs that would change a registered number or let an evaluation run on an incomplete or stale freeze; (3) tests that would pass with a plausible wrong implementation; (4) the rulings: say which you reject and why; (5) frozen files unchanged.

Output exactly:
VERDICT: approve | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
