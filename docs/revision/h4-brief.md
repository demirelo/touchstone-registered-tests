# Brief for the sealed H4 session (design draft 7, 5.3)

You write one attack family, H4, for a simulated verification market. You work alone, in your own clone of the repository at the tag `h4-base`: the defender-freeze commit, where every defending rule is frozen (the factorial rules, the comparator C*, and the tuned whole systems). Your job is to find the strongest attack you can against these defences. Nobody in the project reads your family until the evaluation report; write it so it stands on its own.

## What you may read

- The frozen defences: the rule implementations under `sim/mechanisms/`, the rule set `sim/rules_v2.py`, the frozen comparator `experiments/v2/comparator.json`, and the tuned files `experiments/v2/tuned_*.json`. The fixed pair is tol = 0.16, L = 10.
- The family interface: `sim/policies/families.py` (`Family`: a name, the knob names in coordinate order, bounds for the bounded knobs, a factory that turns a knob dictionary into a policy, and `Family.project`, the truthful projection that clips every claim to the effort).
- What a policy observes: `sim/policies/base.py` (`ProviderView`: its own history across identities, the round, its own parameters, and an identity token usable only for equality).
- The development simulator and data: `sim/`, the development instances (`headline`, `dev0`, `dev1`) and development seeds (dev-train 1000-1004, dev-val 2000-2019), the existing attack families (`sim/policies/`), and their development results in the repository.
- The scoring definitions: design sections 6.1 (normalised gain) and 6.4 (references), in `docs/superpowers/specs/2026-10-22-revision-program-design.md`, and the admissible class of rules (`docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md`, section 4.0).

The source is for you, the author; the running policy sees only the provider view and the public constants (design 5.1): the rule's horizon `T` and ban length `L`, injected when your family is built. No remaining global budget, no other identity's rank, no simulator internals.

Do not read `sealed/` or any other clone's `sealed2/`. Do not call any paid API. Use the CPU of your own machine only, at most 8 core-hours in total for your development runs.

## Resource envelope

- The family has at most 15 knobs, every one either bounded with finite `(lo, hi)`, `lo < hi`, or binary and listed in `BINARY`; `clip` is the last knob and binary.
- The family must support `Family.project` (the default clips `clip` to 1).
- Your family is evaluated as an X7-SC cell: the X7-SC search budget (5 restarts x 600 evaluations on dev-train), the same twin search, and bounded Sobol corner controls (512 points over your knobs, de-duplicated, with the all-low and all-high corners and their truthful projections). It is never enumerated over every corner.

## What you write

`sealed2/h4/family.py`, exporting exactly:

- `make_family(T: int, L: int) -> Family`, returning a `Family` named `"H4"` within the envelope above.
- `BINARY: tuple[str, ...]`, the names of the binary knobs, `"clip"` included.

`sealed2/h4/containment.md`: a short note saying which existing families, if any, your family contains as special cases, and how (the knob values that reproduce them).

## How you check it

```bash
uv run python scripts/h4_check.py --bundle sealed2 --defender-commit "$(git rev-parse HEAD)"
```

It imports your family at two constant pairs and checks the envelope, runs a search against F000, F111, and C* on the development instances, measures one full-budget H4 search and one full-budget X7-SC search (each with its controls) against F111 on the headline market, writes `sealed2/h4/check.json` (with that timing payload) first, and then prints one JSON line, the export record: `bundle_sha256`, `commit`, and the timing payload. A non-zero exit means the load check failed: fix the family and run it again.

## How you finish

Run the check last, after your final change to `family.py` or `containment.md` (the check writes `check.json`, which the bundle hash covers), then commit without changing the bundle:

```bash
git add sealed2 && git commit -m "H4 bundle"
git rev-parse HEAD
```

Print, as your last message, the commit hash and the export record line exactly as the last `h4_check.py` run printed it (it carries `bundle_sha256`). The author copies that line without opening your bundle. Do not push.
