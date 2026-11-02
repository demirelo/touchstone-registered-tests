# Protocol v2 review, round 1 (read-only; no paid APIs; do not read `sealed/`, `sealed2/`, or `~/touchstone-h4`; reasoning effort high; under 1,500 words)

Review the protocol before the lock: `experiments/protocol-v2.yaml` (written by `scripts/lock_v2.py --write`, `--check` ok) and `docs/revision/predictions-v2.md`. Design: `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 7, accepted); operations plan: `docs/superpowers/plans/2026-10-25-revision-operations.md`; the record of what was done: `docs/revision/operations-ledger.md`, `docs/revision/lessons.md`, `docs/revision/h4-decision-record/`, `experiments/v2/` (promoted inputs). Code commit 627a2de; this branch adds only data and documents since then.

Check with evidence:
1. Every bound value follows from its source (hashes, branch two20k, cuts 3, kappa Q1 0.5 and Q4 0.25 from `kappa_effective`, the H4 commitment, the cost, the approval sentence); run `uv run python scripts/lock_v2.py --check` if useful.
2. The departures from the plan, each recorded in the ledger. Say for each whether it compromises a confirmatory claim, and what must change before the lock if so:
   a. The executor (not the author) launched the H4 session resume; the bundle was not read; the executor committed it in the author's clone (`git add`/`commit` only) because the session's sandbox made `.git` read-only, and recomputed the bundle hash (equal to the session's export record). The protocol binds the clone commit aa28ed4; the export record's `commit` field is c5227a0 (the HEAD at check time, before the commit).
   b. Coverage (Operation 4) ran before the decision after the H4 timing. That decision first stopped (development 12.73 USD) because coverage was counted as spent and as remaining work; it was recomputed on the ledger as it stood before coverage (`docs/revision/h4-decision-record/`), giving cuts 3 and total 49.16 USD. The actual development spend is 11.42 USD (cap 12).
   c. The coverage pools were built by an orchestration driver (`results/pods/cov_driver.py`, quoted in the ledger) that calls the frozen `sim.calibration_v2.build_pool` on 25-seed slices, because the frozen `build_market_pool` exceeded pod memory at 20,000 seeds; its pool file was byte-identical to the frozen builder's on a 40-seed pool. The dev0 pool was rescued on its pod by fetching git history into a shallow clone (code unchanged).
   d. Tuning ran B3-t and R3-t in parallel with the comparator selection.
3. The predictions: are they derived from development evidence only, correctly quoted, and stated so that the report can score them? Note any prediction that the cited evidence does not support, or that a decision rule makes unscorable.
4. Anything that must be fixed before the author signs, stamps, and tags `protocol-v2`.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with the file, the exact change, and the reason with evidence.
CONFIDENCE: 0 to 1.
