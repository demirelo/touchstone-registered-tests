# Reset experiment plan draft 5: internal review round 6 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Draft 4 of `docs/revision/reset-experiment-plan.md` had your consensus (rounds 1-3) and the author's approval (cap 10 USD). A Fable 5.2 review of the driver and plan (`docs/revision/roster/fable52-reset-driver-r1.md`, triage `docs/paper/fable52-triage.md`) and two reproduction runs led to draft 5. Rounds 4 and 5 (both reject; `docs/revision/roster/{sol,astra}-reset-plan-r5.md`): `docs/revision/roster/{sol,astra}-reset-plan-r4.md`; commits 2220287 (diagnostics, doubling ground truth) and HEAD respond. Check each round-4 correction. The driver is `docs/revision/followup/reset_followup_v2.py` with tests beside it (48 pass). Reproduction outputs: `/Users/oemer.demirel/Projects/touchstone/results/v2/followup-repro` (Mac) and `.../followup-repro-linux/run` (Linux amd64 container); registered records in `.../eval/all`.

Check: (1) is replacing the draft-4 bit-identity rule by the draft-5 criterion (exact parts plus 1e-9 tolerances, pod gate) justified by the evidence, and is it a recorded deviation rather than a silent loosening; (2) do the driver fixes (pairing, code, salt, inputs, acceptance, inventory environment, output path) close Fable's findings 1, 2, 5-8, and does `compare()` implement the criterion; (3) are the added diagnostics, reverse switch, doubling ground truth, market sensitivity, and all-six-markets scoring well specified; (4) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.
