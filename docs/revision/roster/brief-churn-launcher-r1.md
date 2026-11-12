# Honest-churn launcher: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

The churn arm's plan (draft 6, `docs/revision/churn/churn-plan.md`) reached consensus earlier; its driver is `docs/revision/churn/churn_v2.py` (32 tests pass). Its launcher draft predated the reset launcher's review rounds r9 to r18, so the launcher was regenerated from the final, reviewed `reset_pod.sh` with a small set of edits.

Files:
- `docs/revision/churn/churn_pod.sh` (the launcher; installed copy `results/pods/churn_pod.sh`, identical) and the reviewed base `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh`. Review the diff: `diff /Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh docs/revision/churn/churn_pod.sh`.
- `docs/revision/churn/test_churn_pod_harness.sh` (16 offline scenarios: the 14 of the reset harness plus a driver cap stop and a negative PRIOR) and its log `/Users/oemer.demirel/Projects/touchstone/results/pods/logs_harness/churn_harness3.log`.
- The bundle `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-churn-bundle/` (the reset bundle plus the registered fresh0 R3 D2+H3 evaluate and doubling records for the gate); a read-only check with the driver's own functions found all 138 inputs with matching hashes, pairing and configs ok.
- The reservation in `docs/revision/budget-ledger.json` (churn-pod, 10.40 USD = 1.3 x the 8 USD stop cap; the plan's 4.43 USD estimate padded to 5.54 would not cover the watchdog bound).

Rulings to accept or reject:
1. CAP passed to the launcher is the plan's stop cap, 8 USD (soft deadline at the price ceiling; watchdog at 1.3 x).
2. The driver's `--prior-usd` gets PRIOR (recorded spend of earlier launches, set by the operator) plus this launch's deleted attempts at the ceiling.
3. A driver cap refusal is reported as "STOPPED BEFORE <stage> (cap, driver admission)" by matching "stopped between stages" in the last 5 log lines; anything else is RUN FAILED.

Check: (1) every edit preserves the reset launcher's safety behaviour (creation, price, watchdog, deletion, locks, spend records); (2) the remote script calls the churn driver correctly (gate only first with --require-identical; stages; flags; output dir; the verify paths gate-p0, p0.01, p0.05 match what the driver writes, including where each inventory lies); (3) the harness exercises the new paths and passes; (4) defects the harness misses.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
