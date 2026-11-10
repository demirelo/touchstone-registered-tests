You are an independent reviewer for a research project (a pre-registered simulation study, "Touchstone"). Give your own opinion, review, and feedback. Be adversarial and specific; say where you are unsure. Read only: do not edit files, run paid services, or start any pods. Do not read anything under `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`.

Repository worktree (your working directory): /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79
Registered result records (read-only): /Users/oemer.demirel/Projects/touchstone/results/v2/eval/all

## What to read
1. `docs/revision/reset-experiment-plan.md` (draft 4): a planned follow-up experiment (18 new search cells, about 2 USD of cloud compute, cap 10 USD). Section 3 is the execution contract; its "Validation before spend" (a) says the driver must reproduce the registered `headline@rho0.2|F111|D2` search and evaluation with "identical selected knobs and per-seed gains. If not identical, stop and report."
2. `docs/revision/followup/reset_followup_v2.py` and `docs/revision/followup/test_reset_followup.py`: the driver and its tests. It reuses the frozen stage functions of `scripts/revision_v2.py` (frozen at tag protocol-v2; do not propose edits to frozen files under scripts/, sim/, tests/: a code freeze allows only docs/ and experiments/v2/).
3. `docs/revision/followup/budget_followup.py` and its test: a wrapper that adds a budget category over the frozen `scripts/budget_v2.py`.
4. As needed: `scripts/revision_v2.py` (stage_search, stage_evaluate, stage_doubling, menu, reference_of, _run_one, expected_upstream).

## Measured facts (from commands already run)
- Validation (b), a smoke-size end-to-end run of one fresh-market cell through the driver, passed.
- Validation (a) was run twice, comparing against the registered record (produced on Linux amd64 cloud pods):
  - Mac arm64 run: same config hash, salt hash, runner hash, budget, rule params; same episode count (15,660) and same twin-search best value; selected knobs differ at max relative 2.5e-13; per-seed gains differ at max absolute 2.0e-14 (mean gain 0.0361473 in both); 0 of 200 seeds bit-identical.
  - Linux amd64 Docker container on the Mac (emulated x86, ubuntu:20.04, uv-chosen Python 3.15.2, numpy 2.5.4 from the lock): knobs max relative 2.6e-13, gains max absolute 2.0e-14, 0 seeds bit-identical.
  - The pods' exact Python version is not recorded in logs found so far. An earlier recorded deviation: market configurations computed on Linux pods differ from the Mac by 1 ulp in 2 values.
- Outputs: /Users/oemer.demirel/Projects/touchstone/results/v2/followup-repro and .../followup-repro-linux/run.

## Questions
1. Given the plan's "identical or stop" rule and these facts, what should the author do next before spending money? Give your recommendation and why, including whether the rule was well chosen and what a correct pass criterion would be.
2. Review the driver and its tests: correctness bugs, dependency or hash-check gaps, ways it could produce records that silently differ from the registered stages, or misuse of the frozen functions. Rank by severity, cite file:line.
3. Anything in the plan's design (estimand, analysis, expectations, cost) that you think is wrong or weak.
4. Your confidence in each main point.

Reply with: (1) recommendation, (2) ranked findings with file:line, (3) plan concerns, (4) confidence. Keep it under 900 words. Start your reply with one line naming your model id.
