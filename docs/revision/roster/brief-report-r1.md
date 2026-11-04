# Operation 8: second registered evaluation, report review round 1 (read-only; no paid APIs; do not read `sealed/`, `sealed2/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

The eight evaluation pods ran at tag `protocol-v2` (d5e602e, draw block 974451). `results/pods/post_eval.sh` merged their records into `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all`, built `/Users/oemer.demirel/Projects/touchstone/results/v2/report/report.{json,md}` with `scripts/report_v2.py`, and ran its `--check` (exit 0). Its log is `/Users/oemer.demirel/Projects/touchstone/results/v2/post_eval.log`.

One deviation, chosen by the author: the six fresh markets were recalibrated on Linux x86 pods, while `results/v2/draw/instances.json` holds the arm64 calibration. Between 1 and 6 provider values per fresh market differ by one unit in the last place. The report therefore reads `results/v2/deviation/instances_container_configs.json`, which `docs/revision/deviation/cfg_ulp.py` writes after it checks that (a) a Linux container reproduces each pod's config hash, (b) every differing value is within 1 ulp of the registered one, and (c) strict verify passes with the reproduced configs (`results/v2/deviation/cfg_ulp_all.json`). The headline market uses the registered configs and passes strict verify. A second change: the author raised the evaluation cap from 40 to 43 USD (`docs/revision/budget-ledger.json`); no analysis changed.

Check only:
1. Each of Q1 to Q4 in the report applies the decision rules of `docs/superpowers/specs/2026-10-22-revision-program-design.md` sections 9.1 to 9.4 and `experiments/protocol-v2.yaml` as registered: estimands, interval and test level (kappa or nominal, labelled), Holm family of six for Q4 with missing market p = 1, dependency labels, and claim scope.
2. No cell is missing or "unavailable" without a label, and every registered cell of the manifest is present.
3. The deviation handling: is the 1-ulp substitution sound and fully disclosed, and could it change any reported decision?
4. Any number in `report.md` that does not match `report.json`.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line or JSON path, or "none".
CONFIDENCE: 0 to 1.
