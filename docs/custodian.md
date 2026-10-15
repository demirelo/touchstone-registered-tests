# Instructions for the custodian (the separate session that writes the sealed bundle)

## 1. Who you are and what you must not see

You are the separate AI session of spec section 6.1. You write the sealed held-out bundle before the lock and you never read any rule-design work. Work from a clone of this repository at the lock-candidate commit: it contains no proposed rule, and it is the code your bundle must run against. The author does not read your bundle until the unseal.

## 2. What to produce

The bundle is a directory, `sealed/`, with exactly the files that `sim/sealed.py::BUNDLE_FILES` expects:

- `sealed/README.md`: what the bundle contains, and the access log (who opened or changed what, and when).
- `sealed/h1_prompt.txt`: the H1 system prompt. It replaces the development `ACTOR_INSTRUCTIONS` in `sim/llm_actor.py` through `scripts/h1.py --prompt`. The prompt is part of every cache key, so H1 runs with it never replay a development response; the H1 cache lives under `experiments/cache/h1/<backend>/`, never under `sealed/`. The prompt must describe the provider role, the answer schema, and the goal, and must not name any rule.
- `sealed/h2/family.py`: a module that defines `H2`, an instance of `sim.policies.families.Family` (constructor `Family(name, knobs, bounds, factory)`) with knob domains, a claim map that permits claims below effort, and the binary `clip` knob last, so that H2 contains its twin by construction; the registered starts, the exact key, and the knob key follow `experiments/families.md`. The module also defines `CONTAINMENT`, a string. Use absolute imports only (`from sim.policies.families import Family`), never relative ones.
- `sealed/h2/containment.md`: whether H2 contains D2, is contained by it, or is non-nested, and which observation or memory it uses that D2 cannot. If H2 contains D2, `family.py` also defines `embed_d2(knobs) -> knobs`.
- `sealed/final_eval_seeds.json`: a JSON list of at least 40 distinct integers in `[10000000, 20000000)`. That range is disjoint from dev-train, dev-val, calibration, and the coverage block (3,000,000 to 6,600,000). The first 20 or 40 are used, as `coverage_consequences.final_eval_n` says, and the first 10 for H1.
- `sealed/identity_salt.hex`: 32 random bytes as 64 hex characters. Its SHA-256 goes into `experiments/locked.yaml` as `identity_salt_sha256` before the lock commit. The file itself stays sealed until the evaluation freeze; the author then exports it as `TOUCHSTONE_IDENTITY_SALT` for the final-eval runs.
- `sealed/b1_check.json`: the result of the checks in section 4, pass or fail per check, with the commands used.

The seeds, the salt, and the containment statement are never repaired after the unseal (only the prompt and the family can be, section 6).

## 3. The commitment

On the finished bundle, run:

```bash
uv run python -c "from sim.sealed import bundle_hash; print(bundle_hash('sealed'))"
```

Send that hash (`sealed_bundle_sha256`) and the salt hash (`identity_salt_sha256`, the SHA-256 of the 32 bytes) to the author for `experiments/locked.yaml`. Keep the bundle outside the repository until the unseal, and keep the access log in `sealed/README.md`.

## 4. Checks you run before the lock (B1 only)

Export your bundle directory so the frozen registry loads your family without any edit:

```bash
export TOUCHSTONE_SEALED_DIR=/path/to/your/sealed
```

Then run each command as written:

```bash
uv run python -c "from sim.registry import available_families; f = available_families()['H2']; print(f.name, len(f.corners()))"
```
Your family must load as `H2` through the registry (the test suite's own fixtures do not read your directory).

```bash
uv run python scripts/h1.py --backend fake-honest --rules B1 --smoke --out /tmp/b1 --prompt $TOUCHSTONE_SEALED_DIR/h1_prompt.txt
```
The smoke market calibrates itself. A non-smoke run needs `--calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --max-calls 2000`.

```bash
uv run python scripts/calibrate.py --seeds 2 --out /tmp/cal_locked.json
uv run python scripts/sweep.py --stage all --sections heldout --rules B1 --select B1_H2 --calibration /tmp/cal_locked.json --smoke --out /tmp/b1_sweep
```
One H2 cell against B1 through every stage, with the smoke budget on the locked market.

Record pass or fail and the commands in `sealed/b1_check.json`. B1 reveals nothing about the proposed rule.

## 5. At the unseal (week 5)

The bundle enters the repository under `sealed/`. The author runs:

```bash
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11 --proposed proposed
```

That checks the tree and the bundle hash. No registration step exists: the frozen registry (`sim/registry.py`) finds `sealed/h2/family.py`, the final-eval seeds, and the prompt by itself. The author then runs the comprehension fixture, H1, H2, and the twins on the frozen rule and the baselines on the final-eval namespace (the run book lists the commands), then `scripts/check_claim.py`.

## 6. Repairs

A repair after the unseal is a complete replacement file under `sealed/patches/` with an entry in `sealed/patches/log.json`:

```json
{"<patch file>": {"sha256": "<hex>", "replaces": "<bundle file: h1_prompt.txt or h2/family.py>", "demotes": ["<rule>|<family>", "..."]}}
```

You write it, it is limited to interface errors, and it is logged and reported. The original bundle is never edited (`bundle_hash` ignores `patches/` and import artifacts). The frozen code reads the replaced file through `sim.sealed.effective_path`, which applies a patch only when its hash matches the log. A repair that changes any H1 or H2 decision on a dev-val seed demotes the affected cells to exploratory: list them in `demotes`, and `scripts/check_claim.py` marks them INCONCLUSIVE.

## 7. Timeline

Bundle complete by 2026-10-27. Commitment hashes to the author by 2026-10-27, so the lock commit on 2026-10-28 carries them. Unseal on 2026-11-12.
