VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `docs/revision/followup2/runnerup_v2.py:152`, `:173`.** Check every copied bank file’s current SHA-256 against the original freeze hash. `_required()` takes bank hashes from `inputs.json`; `_validate_new()` checks dependencies against the new reference’s hashes. An in-memory probe accepted a changed bank when the reference recorded its changed hash, although `inputs.json` and the original freeze retained the original hash. Add a refusal test for this case.

2. **Block pod — §2; `docs/revision/followup2/guards.py:108`; plan lines 49–52.** Require the complete set of named reproduction checks, with cell identities and recorded input/code/environment bindings. The gate currently accepts one arbitrary file containing `"pass": true`, including `"identical": false`; an in-memory probe confirmed this. Restore the reset template’s pod command `--reproduce --require-identical` and require that pod result before searches.

3. **§5; `docs/revision/followup2/runnerup_v2.py:304`, `:325`.** Align the execution allowance with the ledger reservation: reserve the full USD 3.00 allowance or limit execution to the granted reservation. Require the allocation timestamp for paid runs and carry prior failed-attempt spending into the remaining allowance. Currently, omission resets the clock, and a new invocation has no cumulative spending check. The benchmark arithmetic reproduces: 17.65 core-hours, USD 1.91 computational estimate, USD 1.99 billed estimate. Current headroom is USD 22.00 for follow-ups and USD 22.131 for the program.

4. **§§1, 3–4; inventory and settings corrections: none.** The narrower estimand, explicit deferrals, matched base/doubled contrasts, unrounded expectation scoring, nominal interval qualifications, exact specification, pinned settings/budgets, and driver-specific inventory address those round 1 requests. Ten shared-analysis tests passed. Tests that require file writes were not rerun under this read-only review.

CONFIDENCE: 0.97.