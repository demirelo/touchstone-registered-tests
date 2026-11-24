Touchstone: two registered tests of age-ranked audit targeting under free identity replacement, with the exploratory follow-ups and a prospective-exploratory replication.

Second registered test: protocol v2, signed tag `protocol-v2`, OpenTimestamps proof attested in Bitcoin. The first test's signed tags (`lock-2026-10-17` with amendments 1 to 4, `freeze-2026-10-18`, `final-eval-2026-10-20`) are in the same history.

Release files (SHA-256):

- `touchstone-v2.tar.gz` (built 2026-11-05, unchanged): all evaluation records of the second test, the draw record with block headers, the instances, the H4 decision and the released H4 bundle, the report with its addendum and the deviation evidence, the promoted inputs, the protocol and its proof, `uv.lock`, and the paper sources as of 2026-11-05 (the current paper sources are in this repository under `docs/revision/paper-v2`), with a manifest. `f6cf682bda2fa5883ff35de00bea2228f2ee8e0c7f2b91168532968fec10812c`
- `touchstone-first-test.tar.gz`: the first test's raw records (final evaluation, registered and proposed-rule sweeps, H1 run); its verdict and summaries are in `docs/final-evaluation-2026-10-20`. `5d93e44c734fe21792c6f32869ec3ac855e52904eb25dc735203ff9d36ebd001`
- `touchstone-followup-paper-inputs.tar.gz`: the paper's scoring inputs and the stability re-evaluation records. `bafc511e889f0f00d597565c12f09bf0eb270f49e5b745dbe4be9d1e9743a648`
- `touchstone-followup-reset.tar.gz`: identity-replacement follow-up records. `e1294b0e93be694930cad6f45ef4c45a64067ed36b5c0d92cbc44c5085178ebe`
- `touchstone-followup-churn.tar.gz`: churn follow-up, p = 0.01 and 0.05. `7498d9b9748a6a4631a44faecde1e6dca465b80d28c9c698ddba494cdf1bebfc`
- `touchstone-followup-churn-mid.tar.gz`: churn follow-up, p = 0.02 and 0.03. `4bea4d375cede183d7de8918df9128e1d4bf2c231d7f8187a55488954b0c85f5`
- `touchstone-followup-runnerup-convergence.tar.gz`: runner-up comparator without churn, and the convergence rerun. `f0f33750fb7f8b56431f34d8c7efc1290f162a167110c2011e30d48ec5f94f5f`
- `touchstone-replication.tar.gz`: run records of the prospective-exploratory replication (1426 files, record digest `51086341e028c820f2b5a0092639554e5844523a9526aa050862ef245b31efdf`). `ad99ef811a77300366fed401ed4c5a52e79f3726f9e519734e818b0564faa35e`

Each archive other than `touchstone-v2.tar.gz` holds a MANIFEST.json with the SHA-256 of every packed file. Check them with `uv run python docs/revision/release/followups.py --check <folder with the archives>`.

Reproduce the second test's report on a clean clone:

    uv run python docs/revision/deviation/reproduce_deviation.py --artifact touchstone-v2.tar.gz --repo https://github.com/demirelo/touchstone-registered-tests

It checks the artifact against the signed tag, checks that the substituted fresh-market configurations differ from the registered ones by at most one unit in the last place (the disclosed deviation), and runs the tagged report's check. Exit 0 means the report is reproduced.

Check the replication's paper extract against its run records: unpack `touchstone-replication.tar.gz`, copy `docs/revision/followup3/replication-analysis.json` to `touchstone-replication/followup3-rep/analysis.json`, and run

    uv run python docs/revision/followup3/replication_extract.py --out touchstone-replication/followup3-rep --manifest experiments/v2/replication-manifest.json --draw experiments/v2/replication-draw.json --check docs/revision/followup3/replication-extract.json

Expected: "ok: the extract rebuilt from the run records is byte-identical; records 1426 files, digest 51086341…". The paper's numbers are regenerated and checked by the scripts in `docs/revision/paper-v2`, `docs/revision/posthoc`, `docs/revision/audit`, `docs/revision/followup2` and `docs/revision/followup3`.

Known limits of the record archives: the inference audit's stability input (`v2/deviation/stability` in the paper-inputs archive) is inferred from `stability.py`, not recorded in a command line; the reset follow-up's reference-replacement cells (`docs/revision/posthoc/reset_reference/cells_fresh*.json`) are committed, but the bundle they were computed from is not shipped; the per-seed lottery inputs are committed in `docs/revision/posthoc` (`lottery_seeds.csv`, `lottery_train.csv`).
