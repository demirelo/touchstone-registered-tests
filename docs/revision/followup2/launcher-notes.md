# Follow-up Runs A and B: the shared pod launcher (notes for review; no spend)

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

1. **Run B's Mac gate evidence is stale (blocker before any B launch).** Each Mac gate record binds the job provenance,
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
   Ruling (for review): reserve the bound, `python3 docs/revision/followup/budget_followup.py --reserve runner-up-1 3.12`
   (grant 3.90) and `--reserve convergence-1 4.42` (grant 5.525); `check_grant` against the stop cap is then not the right
   test and is not used by the launcher. The launcher refuses unless a reservation tagged `<run tag>-<n>` covers HARD x CAP
   minus PRIOR. The follow-up category cap is now 72 USD (author's approval of 2026-11-12), so both fit.
3. **PRIOR comes from the ledger, not the operator.** The drivers count earlier launches from the ledger rows whose tag
   starts with the run tag (`guards.ledger_spend`). The launcher uses the same rule for its deadlines and refuses a PRIOR
   environment variable, so the two can never disagree. Spend must therefore be recorded with a tag starting
   `runner-up-` or `convergence-`.
4. **One push of the attempts file and the ledger.** The plans say "before every paid driver call". Both files are fixed
   for the pod's life (attempt events are written only when a pod is created or deleted; the ledger changes only by the
   operator after a launch), so the launcher pushes both once, before the remote script starts, and every step reads
   those copies. The admission therefore runs before each step with current inputs.
5. **Step estimates.** `--hours` uses the plans' billed-path figures (table above). The drivers' own per-stage or
   per-round admissions run inside each step, so a low launcher estimate cannot let a later stage start over the cap.
6. **Cap.** The launcher refuses a cap above the plan's (A 3.00, B 4.25); a lower cap is allowed (the harness uses it for
   deadline scenarios).
7. **End state parsing (also a latent churn defect).** The polled tail joins several log lines; churn's
   `grep -o '== [A-Z].*'` took everything from the first `== ` (harmless there, since its runs ended RUN OK). This
   launcher takes the last `== <CAPITALS>` segment (harness: a gate failure after earlier lines).
8. **bash 3.2.** The run-specific remote steps are kept in a quoted heredoc assigned to a variable before the remote-script
   heredoc (no nested heredoc and no `case` inside a command substitution, which macOS bash 3.2 cannot parse).

## Pre-launch steps (after review consensus)

1. Commit everything; note the commit C. 2. Run B only: rerun the Mac gate at C into a fresh directory and copy its two
`gate/*__mac.json` into the bundle's `evidence/conv-gate-mac/` (no commit afterwards). 3. Reserve (ruling 2). 4. Build
the code tarball from a clean clone at C (`tar --uid 0 --gid 0`, `COPYFILE_DISABLE=1`) and the bundle tarball. 5.
`DRYRUN=1` guard check. 6. Launch detached with a pid file; record the spend after the watchdog ends plus an hour and the
author's billing check, with a tag starting with the run tag.
