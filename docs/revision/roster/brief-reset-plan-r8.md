# Reset pod launcher: internal review round 8 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 7 (`docs/revision/roster/{sol,astra}-reset-plan-r7.md`) accepted the plan, evidence and bundle and rejected only the launcher. The launcher (outside git) is `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh`, with `runpod.py` and its new test `test_runpod.py` beside it; the code tarball `reset_code.tgz` is rebuilt at commit fdfd83e (contains the copy_inputs fix). Changes: runpod.py ssh/push/pull return the subprocess status (test); an independent watchdog deletes the pod at 1.3x the cap during preparation, run, and pulls; the remote script checks the soft deadline itself before each stage, and the STOP file is verified after creation; pulls are retried and, after RUN OK, both output directories are verified against their inventories before deletion (verify tested on a real directory and on a one-byte change); every deletion, including of an unreachable pod, is verified; the code guard fails closed (checked exit statuses, clean tree, allowed paths, frozen code equal to the tag); dry run passes; negative tests refuse a changed frozen file and a tarball without history.

Check: (1) each round-7 correction is closed; (2) any new defect in the launcher (in particular the watchdog, the deadline arithmetic, the verification, and the cleanup order); (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
