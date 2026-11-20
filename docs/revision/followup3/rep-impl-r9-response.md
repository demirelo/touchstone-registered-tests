# Replication implementation review r9: response ledger

Reviews: `docs/revision/roster/{sol,astra}-rep-impl-r9.md` (Sol reject, one finding; Astra accept, 0.95). Plan of record
unchanged.

| # | Correction (Sol #) | Plan text | Status |
|---|---|---|---|
| P1 | A measured round 1 counts as evidence only when every round-1 field `_rounds_problem` checks is well-formed (round number exactly the integer 1, attack_f, attack_change, reference_f, reference_change finite, best knobs well-formed), so a malformed round 1 combined with a disagreement follows the invalid-record path: not continued in the analysis, rerun on resume (S1) | ruling 10: a malformed round 1 is an invalid record | fixed in `rep_collect._round1_ready`: test_a_malformed_round1_with_a_disagreement_is_an_invalid_record (5 malformations x 5 disagreements, 24 cases, collection and resume; 20 failed first on a5baace, the 4 empty-knobs cases already passed) |

Checks: `uv run --frozen pytest -q docs/revision/followup3/` (229 pass, 1 skip). Launcher and harness unchanged.
