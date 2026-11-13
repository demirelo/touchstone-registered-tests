# Follow-up Runs A and B: shared launcher, internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

Round 1 (`docs/revision/roster/{sol,astra}-f2-launcher-r1.md`): both reject. Every file, command and check of round 1
(`docs/revision/roster/brief-f2-launcher-r1.md`) still applies. Changes since round 1 (uncommitted; see `git diff --
docs/revision/followup2` and the round-1 section at the top of `docs/revision/followup2/launcher-notes.md`):

1. **Inner gate admission (Sol 1, Astra 3).** `convergence_v2.py` `gate_cell` marks `cost_stopped` when the cell's own
   admission refuses round 1 (`round1_gate` "not run"); the gate loop then writes `cost_stop.json` and the inventory, writes
   no gate record, and exits 3. Exit 4 stays for a measured mismatch. Tests: a unit test, and one on the real driver path
   (registered records) where a STOP file appears between the outer and the inner admission; both failed first (the real
   path returned 4).
2. **Reservation identity (Astra 1).** The launcher accepts only the one reservation tagged `<run tag>-<launch tag>` with
   `op` `followup` and a cap of at least HARD x CAP - PRIOR.
3. **Accounting across tags (Astra 2).** NAME is per run (`ts-f2a`, `ts-f2b`): one launch lock, balance baseline and spend
   record per run, so launches of a run cannot overlap and a relaunch is refused until the previous spend is recorded.
   Any other open reservation of the run (an unrecorded earlier launch) and an existing spend row under this launch tag
   refuse the launch. One validated ledger snapshot gives PRIOR and is the pushed copy (no second read of the ledger).
4. **Plans amended (Sol 3, Astra 4).** `runner-up-plan.md` and `convergence-plan.md`: reservation inputs 3.12 and 4.42,
   grants 3.90 and 5.525 (1.3 x the unchanged stop caps 3.00 and 4.25), category cap 72 USD, the stop-cap grant check
   replaced by the sufficient-reservation check, with the reason (churn launcher review r1).
5. **Harness (Sol 2, Astra 5).** 34 scenarios (was 29): wrong category, leftover reservation of an earlier launch, reused
   launch tag, the run-level lock under another tag, a ledger edit after the deadlines (the pushed copy is the snapshot),
   and the real `guards.py` admission inside the generated remote script (gate admitted, runner-up refused by the real
   check). Log `/Users/oemer.demirel/Projects/touchstone/results/pods/logs_harness/followup2_harness2.log`. Before the
   fix, dry runs of the old launcher (`results/pods/followup2_pod.sh.bak-r1`) accepted the wrong-category, leftover and
   reused-tag ledgers; the new one refuses all three.
6. **Stale Run B evidence (Sol 4).** Kept: the launcher refuses Run B until both Mac gate records bind to the launch
   commit; the r1 driver and plan changes also change their binding. The notes require regenerating both records and
   rebuilding the bundle after the final commit.

Tests: `uv run --frozen pytest -q docs/revision/followup2` (97 pass, was 95); harness HARNESS OK (34 of 34). Launcher-notes ruling 7 now
describes the last-segment end-state parse as a defensive change only (churn's parse is correct: only end states are capitalised).

Check: (0) each round-1 correction is resolved; (1) to (6) as in round 1.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
