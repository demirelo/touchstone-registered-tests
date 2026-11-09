VERDICT: accept-with-caveat

CORRECTIONS:
1. **§3, lines 50–78; `scripts/revision_v2.py:725–759`:** Explicitly require a follow-up freeze validator. The frozen `accept()` still checks the full `MAN.required()` set; a new freeze file alone cannot admit the 18 restored cells. Preserve copied records’ original provenance, including their recorded configuration hashes, while checking new jobs against the actual container configurations. Require the smoke integration test to exercise this acceptance path.

2. **§§4, 7, lines 82–86, 120–128:** Itemize diagnostic work and episode reuse. For three rules across seven markets, base/doubled D2+H3 and base D2 require 63 policy evaluations; fixed-policy switches add 42 before reuse. State whether doubled D2 diagnostics are included. “About 70” needs an explicit reuse calculation. Also replace core-hours divided by workers with a stage schedule that includes incomplete worker batches. Using equal benchmark task times, search, evaluation, and doubling alone take approximately 1.77 hours; preparation and idle allowances bring this to 2.37 hours before diagnostics. The USD 3 cap still appears sufficient.

3. **§6, lines 110–116:** Use **S > 0.5** for “most,” or change the wording to “at least half.” State that “met” describes the point estimates under both search budgets; it does not establish that the interval excludes 0.5.

The section-1 means, increments, paired SEs, seeds, reference hashes, and flags check out. D2 validly disables the focal attacker’s replacement action. The finite-search estimand, paired analysis, observation disclosure, reset diagnostics, and removal of option B address the earlier scientific corrections. Round-2 execution and cost requests are addressed in substance, subject to the clarifications above.

CONFIDENCE: 0.96.