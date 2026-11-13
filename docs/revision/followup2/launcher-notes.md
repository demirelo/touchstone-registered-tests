# Follow-up Runs A and B: the shared pod launcher (notes for review; no spend)

**Review round 2** (`docs/revision/roster/{sol,astra}-f2-launcher-r2.md`, both reject). Changes: the launcher takes the
run lock and the spend-record checks before the ledger snapshot, PRIOR and the reservation check (a launch held before
the lock reads the ledger as it is under the lock); `convergence_v2.py` ends the gate at once with exit 4 after a measured
mismatch, so no later cell starts and no later stop can mask it; the pre-launch requirements are listed below.

**Review round 1** (`docs/revision/roster/{sol,astra}-f2-launcher-r1.md`, both reject; rulings 1 and 3 to 8 accepted,
ruling 2 accepted subject to plan amendments). Changes:
- `convergence_v2.py`: a gate cell refused by its own admission before round 1 (`round1_gate` "not run") now exits 3 with
  `cost_stop.json` and no gate record; exit 4 only for a measured mismatch (two tests, one on the real driver path with a
  STOP file appearing between the outer and inner admission; both seen failing first, the real path returned 4).
- Launcher: NAME is per run (`ts-f2a`, `ts-f2b`), so one launch lock, baseline and spend record per run; this launch's
  reservation is the one tagged `<run tag>-<launch tag>` with `op` `followup`; any other open reservation of the run (an
  unrecorded earlier launch) or an earlier spend row under this launch tag refuses the launch; one validated ledger snapshot
  gives PRIOR and is the pushed copy.
- Both plans amended (reservation inputs 3.12 and 4.42, grants 3.90 and 5.525, stop caps unchanged, category cap 72 USD,
  the stop-cap grant check replaced by the sufficient-reservation check, with the reason).
- Harness: wrong-category reservation, leftover reservation of an earlier launch, reused launch tag, the run-level lock
  under another tag, a ledger edit after the deadlines (the pushed copy is the snapshot), and the real `guards.py`
  admission inside the generated remote script.

Launcher `docs/revision/followup2/followup2_pod.sh` (installed copy `results/pods/followup2_pod.sh`, identical), harness
`test_followup2_pod_harness.sh` (copy in `results/pods/`). Generated from `results/pods/churn_pod.sh` (reviewed in churn
launcher rounds r1 and r2, itself from the reviewed `reset_pod.sh`, r9 to r18). Usage:

    EXPECT=<commit> MAXCPH=0.70 bash followup2_pod.sh <A|B> <code_tgz> <bundle_tgz> <tag> <cap_usd> <local_out>

## What each run does on the pod (plans section 5 to 7)

Before every paid step: the STOP file and the soft deadline, then `guards.py admit` with the plan's cap, `--usd-per-hour`
= MAXCPH, `--started-at` = the live pod's request time (the open `start` event in the attempts file), the pushed attempts
file and ledger, `--run-tag`, `--hours` (the step estimate), `--stop-file /root/STOP`, `--soft-deadline`. Exit 3 is a stop
("STOPPED BEFORE <step> (cap, admission)"), any other non-zero exit is "RUN FAILED at admission before <step>".

| Run | Step | `--hours` (source) | Command | End states |
|---|---|---|---|---|
| A | reset gate | 0.61 (plan 5: reproduction gate 0.61 h) | `reset_followup_v2.py --reproduce --require-identical --out results/v2/followup2-a-pod-gate` + bundle inputs | `"gate_ok": false` in the log: GATE FAILED; other error: RUN FAILED |
| A | runner-up | 2.65 (3.56 billed - 0.61 gate - 0.30 preparation and tail) | `runnerup_v2.py --stage all --workers 12 --site pod --out results/v2/followup2-runnerup --reset-mac <bundle>/evidence/a-gate-repro --reset-pod results/v2/followup2-a-pod-gate --doubling-evidence <bundle>/evidence/a-gate-dbl` + paid flags | exit 3: STOPPED BEFORE <stage from its JSON> (cap, driver admission); other: RUN FAILED |
| B | convergence gate | 1.06 (plan 6: gate cells serially 1.06 h) | `convergence_v2.py --gate --site pod --cells headline@rho0.2|F111|X7-SC|profit,fresh1@rho0.2|F111|D2+H3|profit --out results/v2/followup2-conv` + paid flags | 3: STOPPED (driver admission); 4: GATE FAILED; other: RUN FAILED |
| B | convergence | 2.24 (3.60 billed - 1.06 gate - 0.30) | `convergence_v2.py --workers 16 --site pod --out results/v2/followup2-conv` + four `--evidence` (two Mac records from the bundle, two `gate/*__pod.json` from this pod) + paid flags | 4: GATE FAILED (round 1 differs); other non-zero: RUN FAILED; cells stopped by the cap end with exit 0 and keep their frozen estimates (plan 6) |

Bundle inputs on every driver call: `--src <bundle>/eval-all --draw --instances --cfgs --addendum --report` (every flag
checked against each driver's argparse). After RUN OK the launcher pulls and verifies every output directory:
A `followup2-a-pod-gate` and `followup2-runnerup`, B `followup2-conv`. Each driver writes one `inventory.json` at the
directory root, last, listing every file except `inventory.json`, `*.lock`, `*.tmp` (`guards.inventory`,
`reset_followup_v2.inventory`). The verifier checks every listed record's hash and also that every file in the directory
is listed, so no file outside an inventory goes unchecked (the churn `run.json` lesson; here `run.json`, `cost_stop.json`,
`cost.json` and the gate records are inside the inventories).

## Bundle

`results/v2/followup2-bundle/` (880 MB; outside git): `draw/`, `deviation/cfg_linux.json`, `report/{report,addendum}.json`
(each byte-equal to the registered file), `eval-all/{freeze,reference,evaluate,doubling}` (whole registered directories),
`eval-all/search/` (the 140 search records the drivers' own input functions name for both runs, plus the headline F111 D2
record that the reproduction comparison reads), and `evidence/`: `a-gate-repro` (= `results/v2/followup2-a-gate-repro`),
`a-gate-dbl` (= `followup2-a-gate-dbl`), `conv-gate-mac/*__mac.json` (= `followup2-conv-gate/gate/`). Checked offline with
the drivers' functions (scratchpad `check_bundle.py`): Run A's Mac reproduction and doubling evidence verify against the
bundle with the comparisons recomputed; spec, bank inputs, pairing and budgets resolve; Run B's 19 cells resolve.

## Rulings and open questions for the review

1. **Run B's Mac gate evidence is stale (blocker before any B launch; kept after r1).** Both current records bind 51b71d2,
   and the r1 changes to `convergence_v2.py` and `convergence-plan.md` also change their binding (driver and plan hashes).
   After all corrections and the final commit, regenerate both Mac gate records and rebuild the bundle. Each Mac gate record binds the job provenance,
   which includes `git_commit` (51b71d2, the commit when it was made). The pod's main run recomputes the binding at the
   launch commit and refuses on any difference (`check_gate_evidence`), after the paid pod gate. Every later commit changes
   the binding. Ruling: the Mac gate (`convergence_v2.py --gate --site mac --cells <both>`, free, on the Mac) must be rerun
   at the final launch commit, its records copied into the bundle, and no commit may follow before the launch. The
   launcher refuses Run B before any marker unless both Mac records in the bundle pass and bind to EXPECT (harness:
   "Run B is refused when its Mac gate records are not bound to EXPECT"). Run A's evidence does not bind the commit
   (`_verified_dir` compares the provenance without it) and verifies against the bundle now.
2. **Reservation: the plans say the stop cap, the reviewed launcher pattern says the watchdog bound.** Plans: `--reserve
   runner-up-<n> 2.40` (grant 3.00) and `--reserve convergence-<n> 3.40` (grant 4.25), with `guards.check_grant(grant,
   cap)`. Churn launcher review r1 (Sol and Astra): the reservation must cover the watchdog bound, 1.3 x the stop cap.
   Ruling (accepted in r1; plans amended): reserve the bound, `python3 docs/revision/followup/budget_followup.py --reserve
   runner-up-<tag> 3.12` (grant 3.90) and `--reserve convergence-<tag> 4.42` (grant 5.525), where `<tag>` is the launch tag
   given to the launcher; the launcher refuses unless exactly one `followup` reservation `<run tag>-<tag>` covers HARD x CAP
   minus PRIOR. The follow-up category cap is now 72 USD (author's approval of 2026-11-12), so both fit.
3. **PRIOR comes from one ledger snapshot, not the operator.** (r1: the snapshot is also the pushed copy, and NAME is per
   run, so a relaunch is refused until the previous launch's spend is recorded; record it under that launch's tag.) The drivers count earlier launches from the ledger rows whose tag
   starts with the run tag (`guards.ledger_spend`). The launcher uses the same rule for its deadlines and refuses a PRIOR
   environment variable, so the two can never disagree. Spend must therefore be recorded with a tag starting
   `runner-up-` or `convergence-`.
4. **One push of the attempts file and the ledger snapshot.** The plans say "before every paid driver call". Both are fixed
   for the pod's life (attempt events are written only when a pod is created or deleted; the ledger changes only by the
   operator after a launch), so the launcher pushes both once, before the remote script starts, and every step reads
   those copies. The admission therefore runs before each step with current inputs.
5. **Step estimates.** `--hours` uses the plans' billed-path figures (table above). The drivers' own per-stage or
   per-round admissions run inside each step, so a low launcher estimate cannot let a later stage start over the cap.
6. **Cap.** The launcher refuses a cap above the plan's (A 3.00, B 4.25); a lower cap is allowed (the harness uses it for
   deadline scenarios).
7. **End state parsing (a defensive change, not a churn fix).** The polled tail joins several log lines. Churn's
   `grep -o '== [A-Z].*'` is correct for churn: only end states start with a capital letter ("RUN OK", "STOPPED BEFORE",
   "RUN FAILED", "GATE FAILED"), and every progress marker is lowercase. This launcher takes the last `== <CAPITALS>`
   segment instead, so a future capitalised progress marker could not be read as the end state (harness: a gate failure
   after earlier lines).
8. **bash 3.2.** The run-specific remote steps are kept in a quoted heredoc assigned to a variable before the remote-script
   heredoc (no nested heredoc and no `case` inside a command substitution, which macOS bash 3.2 cannot parse).

## Pre-launch steps (after review consensus; none done yet)

1. Commit every correction; note the final commit C. No commit may follow until the launch.
2. **Run B only, required (blocker): regenerate both Run B Mac gate records at C** (`convergence_v2.py --gate --site mac
   --cells headline@rho0.2|F111|X7-SC|profit,fresh1@rho0.2|F111|D2+H3|profit` into a fresh directory, free, on the Mac).
   The current records bind 51b71d2 and the old driver and plan hashes, so the pod would refuse them; the launcher
   refuses Run B until both bind to EXPECT.
3. **Rebuild the bundle:** copy the two new `gate/*__mac.json` into `results/v2/followup2-bundle/evidence/conv-gate-mac/`
   and rebuild the bundle tarball (`COPYFILE_DISABLE=1`).
4. Reserve under the launch tag (ruling 2): `budget_followup.py --reserve runner-up-<tag> 3.12` or
   `--reserve convergence-<tag> 4.42`.
5. Build the code tarball from a clean clone at C (`tar --uid 0 --gid 0`, `COPYFILE_DISABLE=1`).
6. `DRYRUN=1` guard check.
7. Launch detached with a pid file. Record the spend after the watchdog ends plus an hour and the author's billing check,
   under the launch tag.
