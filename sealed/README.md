# Touchstone sealed held-out bundle

Written by the custodian session (spec section 6.1) on 2026-10-17, against the lock-candidate commit d6ee8b6 of the Touchstone repository. The lock commit is on 2026-10-17. The unseal happens after the evaluation freeze; its date is not fixed yet.

The custodian worked from a separate clone of the repository at that commit and read no rule-design work.

## Files

| File | Content |
|---|---|
| `README.md` | This description. It is part of the commitment and is frozen once the bundle hash is computed. |
| `h1_prompt.txt` | The H1 system prompt. It replaces the development `ACTOR_INSTRUCTIONS` of `sim/llm_actor.py` through `scripts/h1.py --prompt`. It describes the provider role, the state fields, the answer schema, and the goal. It names no rule. |
| `h2/family.py` | The held-out family `H2`, an instance of `sim.policies.families.Family`, with nine knobs (eight bounded knobs, then the binary `clip` knob last). It also defines `CONTAINMENT` and `embed_d2`. It uses absolute imports only. |
| `h2/containment.md` | The containment class of H2 relative to D2, the embedding, and the observations and memory that H2 uses and D2 cannot. |
| `final_eval_seeds.json` | A JSON list of 60 distinct integers in [10000000, 20000000), drawn uniformly at random with Python's `secrets` module. The first 20 or 40 are used, as `coverage_consequences.final_eval_n` says, and the first 10 for H1. |
| `identity_salt.hex` | 32 bytes from `os.urandom`, written as exactly 64 lowercase hex characters with no newline. Its SHA-256 (of the 32 raw bytes) goes into `experiments/locked.yaml` as `identity_salt_sha256`. |
| `b1_check.json` | The pre-lock checks of `docs/custodian.md` section 4 (B1 only, fake backends only), pass or fail per check, with the exact commands. |

The access log, `access_log.md`, is in the same directory and is outside the hash by design (`sim/sealed.py::ACCESS_LOG`).

## Commitment

The commitment is `sim.sealed.bundle_hash` over the seven files above, computed with the command in `docs/custodian.md` section 3. The seeds, the salt, and the containment statement are never repaired after the unseal. Only `h1_prompt.txt` and `h2/family.py` can be replaced, through `patches/` and `patches/log.json` (`docs/custodian.md` section 6).

## Use after the unseal

Put this directory at `sealed/` in the repository, or export `TOUCHSTONE_SEALED_DIR` with its path. The frozen registry (`sim/registry.py`) then loads `H2`, the final-eval seeds, and the prompt without any code change.
