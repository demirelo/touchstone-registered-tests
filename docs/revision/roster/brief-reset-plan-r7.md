# Reset experiment plan draft 5: internal review round 7 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Rounds 4-6 rejected draft 5 (`docs/revision/roster/{sol,astra}-reset-plan-r{4,5,6}.md`). Commits since round 6: 30e5353 (identical requires equal objective values; headline diagnostics path), 8d18de4 (the author's decision on card touchstone-reset-repro-pass: the pod gate requires bit identity, `--require-identical`), d865329 (copy_inputs refuses only real conflicts). Driver `docs/revision/followup/reset_followup_v2.py`, 52 tests. Validation evidence through the corrected paths, each with gate.json and an inventory: `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-repro-v2` (headline reproduction), `.../followup-repro-doubling-v2` (doubling ground truth), `.../followup-diag-headline` (headline diagnostics, 200 seeds). Pod launcher (outside git): `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh` with input bundle `.../results/v2/followup-reset-bundle` (168 records; a smoke run of all stages against it passed); dry run passed; a tarball with a changed frozen file is refused.

Check: (1) each round-6 correction is closed; (2) the saved validation evidence meets plan §8 step 3; (3) the launcher implements the plan: gate first with bit identity, stage order, workers, memory check, the between-stage cap rule with a hard stop at 1.3x (the author asked not to kill running jobs), pulls, deletion and verification, and the code guard that replaces lock_v2 --check-commit (which requires HEAD at the tag); (4) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.
