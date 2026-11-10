VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `docs/revision/followup2/guards.py:139`, `:152`.** Evidence validation remains incomplete. An in-memory probe accepted unrelated gates, wrong cell identities, and empty inventories. Require the named reproduction and doubling cells, correct stages, full budgets, current input/provenance bindings, and verified inventory hashes. Include SciPy, CMA, BLAS and LAPACK in environment comparison; `same_environment()` currently accepts changes to these libraries. The pod’s `identical` check is now present, but does not establish that the required experiment produced the evidence.

2. **§2; `docs/revision/followup2/runnerup_v2.py:122`, `:344`.** Check bank copies against original freeze hashes before reference construction, including `--stage reference`. The round-2 correction now protects freeze creation and acceptance. However, direct reference execution still reaches the frozen stage without this check, contrary to draft 3’s stated contract.

3. **Block pod — §§5–6; `docs/revision/followup2/runnerup_v2.py:311`.** Persist failed-attempt spending and reconcile it before each paid attempt. `--prior-spend-usd` defaults to zero; no saved spending record prevents a later pod from receiving the full allowance again. Requiring the allocation timestamp fixes current-pod accounting only. The estimate reproduces: 17.65 core-hours, USD 1.91 computational cost, USD 1.99 billed cost. The USD 3.00 reservation now matches the admission cap.

4. **None — §§1, 3–4 and remaining round-2 corrections.** The bounded estimand answers sensitivity to this development-selected comparator. Matched base/doubled contrasts, unrounded expectation scoring, nominal conditional intervals, and explicit deferrals are appropriate. Live checks passed for all 12 specifications, pairing, budgets, configurations, reference dependency sets, and 108 original bank hashes. Registered base/doubled records have 200 matched seeds per market. The convergence list correctly adds five nesting cells, giving 19 total. Ten shared-analysis tests passed; tests requiring file writes were not run.

CONFIDENCE: 0.97.