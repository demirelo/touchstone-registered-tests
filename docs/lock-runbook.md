# Lock run book

## Compute notes

The simulator is branchy single-thread Python: a GPU does not help, core count does. Set `OMP_NUM_THREADS=1` before any multi-worker run. The search manifest splits across machines with `scripts/sweep.py --stage search --shard K/N` (copy the shards' `search/` directories together before the later stages). The coverage study splits with `scripts/coverage_study.py --cell i --workers 16` (six machines, one cell each; one cell's chunks spread over the pod's cores; measure the per-cell time on the smoke run before estimating), followed by `--merge` on one machine. `scripts/pod_setup.sh` prepares a fresh CPU pod.

## Lock day (2026-10-17), in order

```bash
export OMP_NUM_THREADS=1
uv run python scripts/calibrate.py --out experiments/calibration.json
uv run python scripts/calibrate.py --T 100 --out experiments/calibration_T100.json
uv run python scripts/tune_baselines.py --calibration experiments/calibration.json --rule B1 --out experiments/tuned/tuned_B1.json
uv run python scripts/tune_baselines.py --calibration experiments/calibration.json --rule B2 --out experiments/tuned/tuned_B2.json
uv run python scripts/tune_baselines.py --calibration experiments/calibration.json --rule B3 --out experiments/tuned/tuned_B3.json
uv run python scripts/sweep.py --stage all --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/coverage_study.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --register --workers 8
uv run python scripts/h1.py --backend fake-cheat --rules B1,B2,B3 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/h1_fake
uv run python scripts/h1.py --backend anthropic --rules B2 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_anthropic --pilot
uv run python scripts/h1.py --backend jev --rules B2 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_jev --pilot
cp results/coverage/coverage_report.json experiments/coverage_report.json
cp results/coverage/coverage_cells.json experiments/coverage_cells.json
cp results/pilot_anthropic/pilot_anthropic.json experiments/pilot_anthropic.json
uv run python scripts/lock.py --tuned-dir experiments/tuned --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --coverage-report experiments/coverage_report.json --bundle-hash <from the custodian> --salt-hash <from the custodian> --pilot experiments/pilot_anthropic.json
uv run python scripts/lock.py --tuned-dir experiments/tuned --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --coverage-report experiments/coverage_report.json --pilot experiments/pilot_anthropic.json --check
git add experiments/locked.yaml experiments/tuned experiments/calibration.json experiments/calibration_T100.json experiments/coverage_report.json experiments/coverage_cells.json experiments/pilot_anthropic.json
git commit -S -m "lock: 2026-10-17"
uv run python scripts/check_claim.py --verify-only --verify-lock HEAD --coverage-report experiments/coverage_report.json --proposed none
git tag -s lock-2026-10-17 -m "Touchstone lock 2026-10-17" && git push origin main lock-2026-10-17
```

The lock commit carries `locked.yaml`, the tuned files, both calibrations, the coverage report and selection, and the pilot (spec 6 lists the coverage report as lock-commit content); the verify-only check runs against the committed tree (`HEAD`), after the commit and before the signed tag, so a lightweight tag is never needed (this machine signs every tag). Then post the tag hash to the public timestamp (OSF or AsPredicted) the same day. The coverage study's base entry is about 2.85 million episodes (about a day on 8 cores, or under an hour on six 16-vCPU pods with `--cell`); the conditional n = 40 run starts by itself only when the remedy order reaches it.

## Pods

The tuned files, the calibrations, and the sweep outputs are untracked, so every pod gets them by copy (`rsync` over SSH or `runpodctl send`/`receive`); `<pod>` stands for the pod's SSH address.

```bash
# on each fresh pod: clone the branch being run (HTTPS, no key needed for a public or token-authorized repo), install, and set the thread variable
curl -fsSL https://raw.githubusercontent.com/demirelo/touchstone/plan-2b/scripts/pod_setup.sh | bash -s -- https://github.com/demirelo/touchstone.git plan-2b
# fresh runpod/base CPU images have no uv: install it and put ~/.local/bin on PATH before uv sync; pass --workers as a number
# (nproc honours OMP_NUM_THREADS=1 and returns 1; getconf reports the host's cores, not the pod's share); mkdir -p the target
# directories before rsync (rsync does not create missing parents) and count the copied files before a launch
# from the author's machine: the tuned files and calibrations to every pod
rsync -a experiments/tuned experiments/calibration.json experiments/calibration_T100.json <pod>:touchstone/experiments/
# search shards (N pods), then collect the shards' search/ directories into one results/sweep on the author's machine
ssh <pod> 'cd touchstone && OMP_NUM_THREADS=1 uv run python scripts/sweep.py --stage search --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 16 --shard K/N --out results/sweep'
rsync -a <pod>:touchstone/results/sweep/search/ results/sweep/search/
# the later stages once, on the author's machine (or one pod with the merged search/ directory)
uv run python scripts/sweep.py --stage bank --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/sweep.py --stage reference --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/sweep.py --stage evaluate --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/sweep.py --stage checks --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
# coverage cells (six pods): every pod needs the merged results/sweep (reference records and bank.json); then the cell files come back to one machine
rsync -a results/sweep <pod>:touchstone/results/
ssh <pod> 'cd touchstone && OMP_NUM_THREADS=1 uv run python scripts/coverage_study.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --cell i --workers 16'
rsync -a <pod>:touchstone/results/coverage/cell_i.json results/coverage/
uv run python scripts/coverage_study.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --merge --register
```

## Amendment 1 (2026-10-17), after the lock and before any proposed-rule code

The amendment file `experiments/amendment-2026-10-17.yaml` is binding (clause, extension study, seed block, design and tuning registration, falsification gate); `docs/amendments/2026-10-17-amendment-1.md` explains it. H3 is the public identity-replacement stress test on fresh final-evaluation seeds, never a held-out family. `experiments/locked.yaml` is never edited.

```bash
export OMP_NUM_THREADS=1
# the one end-to-end smoke path (about half an hour); also the throughput measurement for the calendar estimate
uv run pytest tests/test_coverage_ext_script.py -q --runslow
# six pods, one cell each (results/pods helpers; explicit --workers from the API's vCPU count; mkdir -p the targets before rsync; verify 59 reference records, the base report hash, and the selection before launch)
ssh <pod> 'cd touchstone && OMP_NUM_THREADS=1 uv run python scripts/coverage_ext.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --amendment experiments/amendment-2026-10-17.yaml --base-report experiments/coverage_report.json --selection experiments/coverage_cells.json --out results/coverage_ext --cell i --workers 16'
rsync -a <pod>:touchstone/results/coverage_ext/ results/coverage_ext/
uv run python scripts/coverage_ext.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --amendment experiments/amendment-2026-10-17.yaml --base-report experiments/coverage_report.json --selection experiments/coverage_cells.json --out results/coverage_ext --merge
uv run python scripts/amend.py --amendment experiments/amendment-2026-10-17.yaml --report results/coverage_ext/coverage_report_amendment.json --base-report experiments/coverage_report.json --selection experiments/coverage_cells.json --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned
cp results/coverage_ext/coverage_report_amendment.json experiments/coverage_report_amendment.json
uv run python scripts/amend.py --amendment experiments/amendment-2026-10-17.yaml --report experiments/coverage_report_amendment.json --base-report experiments/coverage_report.json --selection experiments/coverage_cells.json --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --check
# the expected delta against the original lock: exactly the amendment's files; record the list in the amendment note, never call it clean
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17 --proposed none
git add experiments/amendment-2026-10-17.yaml experiments/coverage_report_amendment.json docs/amendments
git commit -S -m "amendment 1: registered"
git tag -s lock-2026-10-17-amendment-1 -m "Touchstone amendment 1" && git push origin main lock-2026-10-17-amendment-1
printf 'Touchstone amendment 1\n\ntag: lock-2026-10-17-amendment-1\ncommit: %s\ntag object: %s\namendment_sha256: %s\ncoverage_report_amendment_sha256: %s\n' "$(git rev-parse lock-2026-10-17-amendment-1^{commit})" "$(git rev-parse lock-2026-10-17-amendment-1)" "$(uv run python -c 'import yaml; from sim.amendment import amendment_hash; print(amendment_hash(yaml.safe_load(open("experiments/amendment-2026-10-17.yaml"))))')" "$(shasum -a 256 experiments/coverage_report_amendment.json | cut -d" " -f1)" > docs/lock-2026-10-17-amendment-1.txt
uvx --from opentimestamps-client ots stamp docs/lock-2026-10-17-amendment-1.txt
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-1 --proposed none
```

A draft amendment (registration fields null) refuses every confirmatory `check_claim.py` run; `--verify-only` reports it as unregistered. The proposed rule is designed only after this tag, inside the registered `design` block, and tuned by the registered `tuning` block; the five falsification tests of the `falsification` block are recorded before the freeze tag.

## Amendment 2 (2026-10-17), the post-lock orchestration, before any proposed-rule code

Orchestration only (`docs/amendments/2026-10-17-amendment-2.md`): the proposed rule's post-lock cells and the H3 doubling controls in the manifest, the H3 bank transfer through the registered embeddings, the registered tuning driver, the describe writer, the falsification harness, the rule's contract tests, and the `--bank-from` resolver. No claim, threshold, or registered artifact changes. The expected delta against `lock-2026-10-17-amendment-1` is recorded in the note.

```bash
export OMP_NUM_THREADS=1
uv run pytest -q && uv run pytest tests/test_tune_proposed_script.py tests/test_falsify_proposed.py -q --runslow
uv run python scripts/amend.py --amendment experiments/amendment-2026-10-17.yaml --report experiments/coverage_report_amendment.json --base-report experiments/coverage_report.json --selection experiments/coverage_cells.json --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --check
# the expected delta against the amendment-1 tag: exactly Phase A's files; recorded in the note, never called clean
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-1 --proposed none
git tag -s lock-2026-10-17-amendment-2 -m "Touchstone amendment 2 (post-lock orchestration)" && git push origin main lock-2026-10-17-amendment-2
printf 'Touchstone amendment 2\n\ntag: lock-2026-10-17-amendment-2\ncommit: %s\ntag object: %s\namendment_sha256: %s\n' "$(git rev-parse lock-2026-10-17-amendment-2^{commit})" "$(git rev-parse lock-2026-10-17-amendment-2)" "$(uv run python -c 'import yaml; from sim.amendment import amendment_hash; print(amendment_hash(yaml.safe_load(open("experiments/amendment-2026-10-17.yaml"))))')" > docs/lock-2026-10-17-amendment-2.txt
uvx --from opentimestamps-client ots stamp docs/lock-2026-10-17-amendment-2.txt
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-2 --proposed none
```

## Amendment 3 (2026-10-18), one successor after the F2 kill

`docs/amendments/2026-10-18-amendment-3.md` is binding: the amendment-2 rule stays KILL; one successor R3 with the fresh-identity priority phase; F2 to F5 unchanged; any registered kill ends proposed-rule development. Registration commits the revised `tests/test_proposed.py` (13 tests fail against the old module by design) and the note; the user signs and tags; then the cycle:

```bash
export OMP_NUM_THREADS=1
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-2 --proposed proposed   # expected delta: tests/test_proposed.py
git tag -s lock-2026-10-17-amendment-3 -m "Touchstone amendment 3 (one successor rule after the F2 kill)" && git push origin main lock-2026-10-17-amendment-3
printf 'Touchstone amendment 3\n\ntag: lock-2026-10-17-amendment-3\ncommit: %s\ntag object: %s\namendment_sha256: %s\n' "$(git rev-parse lock-2026-10-17-amendment-3^{commit})" "$(git rev-parse lock-2026-10-17-amendment-3)" "$(uv run python -c 'import yaml; from sim.amendment import amendment_hash; print(amendment_hash(yaml.safe_load(open("experiments/amendment-2026-10-17.yaml"))))')" > docs/lock-2026-10-17-amendment-3.txt
uvx --from opentimestamps-client ots stamp docs/lock-2026-10-17-amendment-3.txt
# the cycle (allow-listed files only): implement R3, then
uv run pytest tests/test_proposed.py tests/test_harness_all_rules.py -q                                            # F1 before anything expensive
uv run python scripts/falsify_proposed.py ... is not run yet: the F2 diagnostic at the prior parameters is the F2 helper on the five dev-train seeds (a kill ends the cycle; recorded in docs/)
uv run python scripts/tune_proposed.py --calibration experiments/calibration.json --sweep-out results/sweep --tuned-dir experiments/tuned --out experiments/proposed.yaml --log results/tuning_proposed_a3
uv run python scripts/describe_proposed.py --params experiments/proposed.yaml --out experiments/proposed_describe.yaml
# fresh results/sweep_proposed: the baselines' 57 search records reused after their hashes verify; the proposed rule's 25 cells, then every later stage for all four rules
uv run python scripts/sweep.py --stage search --sections development,rho_sweep,h3,ablation --rules proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 16 --out results/sweep_proposed
for st in bank reference evaluate checks all_deviators; do uv run python scripts/sweep.py --stage $st --sections development,rho_sweep,h3,all_deviators,ablation --rules B1,B2,B3,proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 16 --out results/sweep_proposed; done
uv run python scripts/falsify_proposed.py --calibration experiments/calibration.json --tuned-dir experiments/tuned --sweep-out results/sweep_proposed --out results/falsification_a3
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-3 --proposed proposed
```

Then the freeze-day sequence below with `lock-2026-10-17-amendment-3` in place of `lock-2026-10-17-amendment-2`, and the evaluation with the same substitution.

## Freeze day (the day the proposed rule is final; the commands show 2026-11-11 as the example date)

Rules for the proposed rule's module `sim/mechanisms/proposed.py`, enforced by `scripts/check_claim.py` (`check_proposed_module`): imports only `sim.mechanisms.base`, `numpy`, `scipy`, `math`, `dataclasses`, `typing`, `__future__`, `itertools`, `functools`, in absolute form; no `__import__`, `exec`, `eval`, `compile`, `globals`, `vars`; no `importlib`, `builtins`, or `sys` calls; no `getattr`, `setattr`, or `delattr` with a dunder or computed name; no `__builtins__`; no access to `__subclasses__`, `__globals__`, `__dict__`, `__base__`, `__bases__`, `__mro__`, `__class__`, `__code__`, `__closure__`, `__loader__`, or `__spec__`. Importing the module, and calling `make(params)`, must change no attribute of any `sim.*` module. Before the freeze tag, the registered sequence of amendments 1 and 2 (`docs/amendments/2026-10-17-amendment-2.md`), in order; a kill in `scripts/falsify_proposed.py` stops here and is reported with its figures:

```bash
export OMP_NUM_THREADS=1
# 1. the registered tuning (36 configurations x 2 families, top 3 rechecked; one 16-vCPU pod or the laptop overnight); writes experiments/proposed.yaml and the logs
uv run python scripts/tune_proposed.py --calibration experiments/calibration.json --sweep-out results/sweep --tuned-dir experiments/tuned --out experiments/proposed.yaml --log results/tuning_proposed
# 2. the describe record (refuses anything but the registered not-expressible audit selection)
uv run python scripts/describe_proposed.py --params experiments/proposed.yaml --out experiments/proposed_describe.yaml
# 3. the proposed rule's sweep: all four rules in one directory (every bank source; the baselines' post-lock re-runs are part of the registered design), every stage
uv run python scripts/sweep.py --stage all --sections development,rho_sweep,h3,all_deviators,ablation --rules B1,B2,B3,proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 16 --out results/sweep_proposed
# 4. the five falsification tests; records f5_bank (the bank F5 used) into experiments/proposed.yaml and writes docs/amendments/falsification-<date>.md
uv run python scripts/falsify_proposed.py --calibration experiments/calibration.json --tuned-dir experiments/tuned --sweep-out results/sweep_proposed --out results/falsification
# 5. verify, commit the three allow-listed files and the falsification record, tag
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-2 --proposed proposed
git add sim/mechanisms/proposed.py experiments/proposed.yaml experiments/proposed_describe.yaml docs/amendments
git commit -S -m "freeze: the proposed rule, its parameters, its description, and the falsification record"
git tag -s freeze-2026-11-11 -m "Touchstone evaluation freeze"
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-2 --verify-freeze freeze-2026-11-11 --proposed proposed
```

## Evaluation (after the unseal, the day after the freeze; 2026-11-12 in the example)

```bash
export TOUCHSTONE_IDENTITY_SALT=sealed/identity_salt.hex   # the variable names the salt file, not its content
# the final sweep takes the development bank of the proposed rule's sweep (verified there; the final H3 cells use exactly the bank F5 tested); pass --bank-from again on any resumed stage
uv run python scripts/sweep.py --stage all --sections heldout --rules B1,B2,B3,proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned --eval-namespace final_eval --workers 8 --bank-from results/sweep_proposed --out results/final
uv run python scripts/h1.py --backend anthropic --rules B1,B2,B3,proposed --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --eval-namespace final_eval --prompt sealed/h1_prompt.txt --out results/h1_final
uv run python scripts/check_claim.py --verify-lock lock-2026-10-17-amendment-2 --verify-freeze freeze-2026-11-11 --sweep-out results/final --bank-from results/sweep_proposed --h1-dir results/h1_final --calibration experiments/calibration.json --tuned-dir experiments/tuned --coverage-report experiments/coverage_report.json --coverage-ext experiments/coverage_report_amendment.json --amendment experiments/amendment-2026-10-17.yaml --proposed proposed --proposed-describe experiments/proposed_describe.yaml   # prints the original and the amended verdict; the final sweep's heldout section also holds the H3 stress-test cells; --bank-from is checked against the frozen f5_bank
uv run python scripts/plot.py --sweep-out results/final --out results/figures --coverage-report results/coverage/coverage_report.json --h1-dir results/h1_final
```

The test that `proposed.py` imports only the base module and mutates nothing runs inside `scripts/check_claim.py`, so no new test file is needed after the lock.

## Amendment 4 (2026-10-20), a one-time lift of the H1 cost cap for the last cell

The H1 final run stopped at the locked cumulative cap (300 USD) with 11 of 12 cells complete (`results/h1_final/h1_summary.json`: `stopped_by` "cost cap 300.0 USD would be crossed", partial cell `proposed|0.1`). Two restarts preceded it: a credit outage at 205.33 USD and one accidental duplicate launch (about two minutes, about 1 USD). `docs/amendments/2026-10-20-amendment-4.md` is binding: the cap becomes 330 USD for this run only, applied with `--max-cost-usd 330` on the same command; no second lift; the twelfth cell is reported whatever it is. Registration commits the note and the roster memos (`docs/` only); the user signs and tags; then the resume:

```bash
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-3 --proposed proposed   # before the tag; expected delta: none (docs/ only); also git show --stat of the registration commit: docs/ paths only
git tag -s lock-2026-10-17-amendment-4 -m "Touchstone amendment 4 (one-time lift of the H1 cost cap to 330 USD for the last cell)" && git push origin main lock-2026-10-17-amendment-4
printf 'Touchstone amendment 4\n\ntag: lock-2026-10-17-amendment-4\ncommit: %s\ntag object: %s\namendment_sha256: %s\n' "$(git rev-parse lock-2026-10-17-amendment-4^{commit})" "$(git rev-parse lock-2026-10-17-amendment-4)" "$(uv run python -c 'import yaml; from sim.amendment import amendment_hash; print(amendment_hash(yaml.safe_load(open("experiments/amendment-2026-10-17.yaml"))))')" > docs/lock-2026-10-17-amendment-4.txt
uvx --from opentimestamps-client ots stamp docs/lock-2026-10-17-amendment-4.txt
# the resume (from a terminal with a 1Password session; the cumulative ledger replays every cached call first)
export TOUCHSTONE_IDENTITY_SALT=sealed/identity_salt.hex
ANTHROPIC_API_KEY="$(op item get r6fm3jl34rgvycqjtng3mshupa --fields label=credential --reveal)" nohup uv run python scripts/h1.py --backend anthropic --rules B1,B2,B3,proposed --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --eval-namespace final_eval --prompt sealed/h1_prompt.txt --out results/h1_final --max-cost-usd 330 > results/h1_final/h1_resume6.log 2>&1 &
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-17-amendment-4 --proposed proposed   # after the tag
# after completion: the full evaluation claim-check command above with --verify-lock lock-2026-10-17-amendment-4 --verify-freeze freeze-2026-10-18 --h1-dir results/h1_final (all other arguments as listed), then plot.py with --h1-dir; separately confirm 12 cells x 10 repetitions, partial [], cost_cap_usd 330.0 in h1_summary.json
```
