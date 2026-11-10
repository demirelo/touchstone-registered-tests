VERDICT: reject

CORRECTIONS:

1. **Blocker—plan §3; scripts/revision_v2.py:365, :894; sim/reference.py:87.** Doubling does not fully re-evaluate the reference menu under churn. Candidates retain cached no-churn profits, which `select_reference` accepts. `reference_change` also subtracts the saved no-churn reference score. Clear those caches and evaluate the frozen candidate under churn on the training seeds. Test both corrections before pod creation.

2. **Plan §3, churn-plan.md:59.** Frozen-reference reuse is acceptable for the stated fixed-reference estimand. A weaker reference can increase measured gain; unequal reference losses can move rule contrasts in either direction. Report attack and reference profits separately. Distinguish reselecting the existing menu, which needs evaluations, from rebuilding its searches; the quoted USD 24.37 prices the latter.

3. **Plan §3, churn-plan.md:41.** The model fairly tests sensitivity to honest identity replacement while keeping provider characteristics fixed. It also resets history and permits escape from false bans, so it does not isolate age information. Rates 0.01 and 0.05 are useful sensitivity settings, with mean identity lifetimes of 100 and 20 rounds; they lack empirical calibration. Remove “newest uninformative most of the time.” Measure whether the focal identity remains newest.

4. **Plan §§5–6, churn-plan.md:94, :106.** Compare base churn results with base no-churn results, and doubled churn results with doubled no-churn results. The stated 0.0207 baseline is the frozen-search contrast; the doubled contrast is approximately 0.02962. Retain the disclosed peek and exploratory label. State that seed intervals exclude search uncertainty and uncertainty across markets.

5. **Plan §§4,6; churn_v2.py:144.** Diagnostics currently use only base winners, although expectation scoring requires base and doubled results. Add doubled-winner diagnostics. Define market pooling, save per-seed counts, and report empty-bin shares as unavailable. Higher newcomer audit rates alone support increased audit exposure, not economic loss.

6. **Plan §3; churn_v2.py:166.** Injection reaches search, twin search, evaluation, and doubling; suffixed IDs and separate directories protect registered records. Before spend, implement and save the p=0 comparison through this injected path, including ID mapping and refusal on failure. The current main function provides no reproduction comparator.

7. **Plan §7.** The USD 4.30 arithmetic checks out. Specify stage worker limits and verify churn memory use against the pod limit. Include reproduction and serial diagnostics in billed time. Require a separate recorded churn allocation, reservation, and enforced USD 7 stop before launch.

CONFIDENCE: 0.96.