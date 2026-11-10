VERDICT: reject

CORRECTIONS:

1. **§5; convergence_v2.py:309–312; guards.py:126–134.** Validate the complete gate binding. The evidence check ignores budget, provenance, stopping settings, SciPy, CMA, and BLAS. An in-memory test accepted evidence with incorrect budgets and settings and a different numerical stack. Require the expected full-budget provenance and gate settings. Compare all recorded numerical dependencies for pod evidence.

2. **§§3,5; convergence_v2.py:306–311,331; guards.py:43–55.** Complete the saved-result binding. It omits the helper, plan, report, posthoc, and registered doubling-record hashes. Inventory hashes do not prevent reuse. In particular, changing the doubled D2+H3 incumbent in the report can leave a nesting cell’s binding unchanged. Bind these inputs and implementation files before accepting evidence or reusing results. This round-2 correction remains incomplete.

3. **§§2,4; convergence_v2.py:88–89,217.** Make `passed_round` respect `min_rounds` and the final outcome. Five added nesting cells already pass round 1 but must continue. A round-1 pass followed by failures in rounds 2–3 currently produces “not passed at the cap” with `passed_round: 1`. An in-memory test confirmed this contradiction. Report a pass only from an eligible round.

4. **§6; convergence_v2.py:211–222,345–347.** Align cost-stop substitution with the plan. The plan says a cell refused admission keeps its frozen estimate. If admission fails after a completed round, the driver evaluates and substitutes that round’s winner. Specify which behavior applies before outcomes exist, then make the driver and analysis agree.

5. **none — §§1–4,6, remaining round-2 corrections.** The bounded search-sensitivity estimand, expectations timing, nominal conditional intervals, and deferrals are appropriate. Analysis now restricts substitutions to selected cells and checks identity, binding, finite gains, and length. Cost checks cover gate cells and first rounds; serial gate scheduling and the USD 3.30 estimate, USD 4.12 margin, and USD 4.25 reservation agree. All 19 jobs pass pairing, configuration, and budget checks; all 111 dependency hashes match. Thirty-five read-only tests pass. The full suite and full-budget reproduction gates were not run.

CONFIDENCE: 0.97.