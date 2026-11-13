# Honest-churn amendment 1 (rates 0.02 and 0.03): plan, launcher change, analysis; internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

The churn arm (plan draft 6) ran at p = 0.01 and 0.05 and is in the paper. External review round 4 (Fable 5.2,
`docs/revision/roster/fable52-paper-r4.md`) found that the two rates bracket the point where honest newcomers' jobs
exceed R3's audit quota; the author chose to add p = 0.02 and 0.03 before Runs A and B.

Files:
- Amendment `docs/revision/churn/churn-plan-amendment-1.md` (only the rate set changes; four expectations 5 to 8 written
  before any run at these rates; cost; steps).
- Launcher `docs/revision/churn/churn_pod.sh` and harness `docs/revision/churn/test_churn_pod_harness.sh` (installed
  copies in `/Users/oemer.demirel/Projects/touchstone/results/pods/`, identical). Changes since the reviewed version
  (ef17139): `git diff ef17139 -- docs/revision/churn/churn_pod.sh docs/revision/churn/test_churn_pod_harness.sh`:
  the RATES setting (validated before any marker; `--rates` on every driver call; each rate directory verified after
  RUN OK) and a defensive end-state parse (the last capitalised marker of the polled tail). The old parse was already correct,
  because only end states start with a capital letter after `== `; a new scenario with several markers passes on both
  versions (checked). Harness run 7 caught a defect in my parse edit (a trailing comment swallowed `; exit 1 ;;`, so a stop
  or failure polled until a timeout); fixed, and a new guard `docs/revision/churn/case_end_check.py` (run first by the
  harness) refuses a `;;` that appears only inside a comment. Harness log
  `/Users/oemer.demirel/Projects/touchstone/results/pods/logs_harness/churn_harness8.log` (24 of 24).
- Analysis `docs/revision/posthoc/churn_block.py` and `test_churn_block.py` (32 pass), commit 2604ce6: `--rates`,
  `expectations_mid` (5 to 8), and a post hoc `review_r4` block (market t intervals, efficiency under attack, audit
  allocation). Draft-6 fields of `churn.json` are unchanged (`git diff 012af60 2604ce6 -- docs/revision/posthoc/churn.json`
  adds only `review_r4`).
- The driver `docs/revision/churn/churn_v2.py` is unchanged (`--rates` existed; its admission prices every p > 0 at 1.33).

Check: (1) the amendment changes only the rate set and its expectations are specific, scorable, and written before any
run; (2) the launcher change keeps every reviewed safety behaviour and passes the rates correctly; the parse fix is right;
(3) `expectations_mid` scores 5 to 8 exactly as written, `--rates` cannot mix the two arms' expectations, and the
`review_r4` block computes what its labels say; (4) the cost and reservation; (5) defects the tests miss.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
