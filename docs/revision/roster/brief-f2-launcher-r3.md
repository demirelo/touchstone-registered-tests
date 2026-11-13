# Follow-up Runs A and B: shared launcher, internal review round 3 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

Round 2 (`docs/revision/roster/{sol,astra}-f2-launcher-r2.md`, on commit 8b2358d): both reject. Every file, command and
check of rounds 1 and 2 (`brief-f2-launcher-r1.md`, `brief-f2-launcher-r2.md`) still applies. Changes since 8b2358d
(uncommitted; `git diff 8b2358d -- docs/revision/followup2`; round-2 section at the top of `launcher-notes.md`):

1. **Run lock before the ledger (Sol 1).** `followup2_pod.sh` takes `NAME.launchlock` and runs the spend-record checks
   before the ledger snapshot, PRIOR and the reservation check; every refusal after the lock releases it, the dry run too.
   A launch held before the lock therefore reads the ledger as it is when it holds the lock. Harness scenario "a second
   launch held before the lock validates the ledger as it is under the lock (r2)": a second launch of the same run and
   tag is held at its tarball guard (a python wrapper) while the first launch runs and ends and its spend is recorded
   (the reservation replaced by a spend row); on resuming it must be refused ("already has a spend record") with one
   creation request in all. Against the 8b2358d launcher (`results/pods/followup2_pod.sh.bak-r2`) the same scenario
   fails (log `/Users/oemer.demirel/Projects/touchstone/results/pods/logs_harness/followup2_r2_old.log`).
2. **Measured gate mismatch ends the gate (Sol 2, Astra 1, 2).** `convergence_v2.py` writes the failed gate record, the
   inventory, and returns 4 at once; no later cell starts. Tests: `test_a_measured_gate_mismatch_exits_4_at_once_and_
   no_later_cell_starts[outer|inner]` (the second cell's outer admission refuses after a STOP file, or its inner
   admission refuses; exit 4, one cell started, the failed record and the inventory, no `cost_stop.json`), both failing
   on 8b2358d with exit 3; `test_without_a_measured_mismatch_a_later_admission_refusal_still_exits_3` keeps exit 3.
3. **Pre-launch requirement (Astra 3).** Not done yet, as instructed; `launcher-notes.md` "Pre-launch steps" lists it as
   a blocker: regenerate both Run B Mac gate records at the final commit and rebuild the bundle.
4. **Case-end guard.** `python3 results/pods/case_end_check.py docs/revision/followup2/followup2_pod.sh` passes ("case
   ends ok") and is the harness's first check.

Commands: `uv run --frozen pytest -q docs/revision/followup2` (100 pass); harness (35 checks) log
`/Users/oemer.demirel/Projects/touchstone/results/pods/logs_harness/followup2_harness3.log`.

Check: (0) each round-2 correction is resolved; (1) to (6) as in round 1.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
