# Design review, round 7 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 1,000 words)

You accepted draft 6 of `docs/superpowers/specs/2026-10-22-revision-program-design.md` in round 6 (`docs/revision/roster/{sol,astra}-design-r6.md`). A second external review (GPT Pro) then found that draft 6 compares duplicate rules and raised 17 further corrections before the lock. The triage, with our check of each finding against the repository, is `docs/revision/gpt-pro-review-r2-triage-2026-10-27.md` (section 1, D1 to D18). Draft 7 applies them; section 14 of the design maps each finding to its section. See the change with `git diff 7a8957c HEAD -- docs/superpowers/specs/2026-10-22-revision-program-design.md`. Context as before (`sim/`, `scripts/`, the simulator spec, the paper, `sim/calibrate.py`, `sim/market.py`, `sim/instances.py`, `sim/intervals.py`, `sim/mechanisms/`, `sim/policies/`, `docs/revision/h4-brief.md`). Part A code was built to draft 6; the "Code" column of section 14 lists what must change.

Check:
1. **D1.** Verify independently that R4 equals R3 and C*/S2 equals C* in every rho = 0.2 market of the program (A_tot from `sim/calibrate.py` `cell_config` and the generator in `sim/instances.py`), and that they differ at rho = 1. Is the fix complete (manifest, Q1, coverage fixtures, checks, costs), and is dropping R4-t right?
2. **Each of D2 to D18:** is it resolved in draft 7 as the triage says, with no narrower reading? Is any finding wrongly accepted, so that draft 7 makes the design worse?
3. **New errors** draft 7 introduces, in particular: the X7-SC reset-or-wait and exposure conditions and their D2+H3 embedding (5.2); the X8-DB specification and its truthful projection (5.2, 6.3); the coalition order with G_tot before the reference (6.3, 6.4); the defence-aware H4 order and envelope (5.3, 11); the Q1 categories and the efficiency condition (9.3); selection with the validation criterion (9.5); the recomputed counts and costs (6.5, 8.1, 8.2, 9.5); the question-to-cells table (8.1a).
4. **Questions 3 to 5 of section 12.**
5. **Code list:** is the "Code" column of section 14 complete?

Accept only if the design, once executed, answers Q1 to Q4 soundly within its stated scope. A material objection must name the section, the effect, the evidence, and the repair; do not reopen points that you accepted in round 6 unless draft 7 broke them.

Read-only sandbox: if you run Python, use `uv run python` with `-p no:cacheprovider` for pytest and set `MPLCONFIGDIR` to a writable path if needed; say what you could not run.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with the section, the exact change, and the reason with evidence.
ANSWERS: questions 3 to 5 of section 12.
CONFIDENCE: 0 to 1.
