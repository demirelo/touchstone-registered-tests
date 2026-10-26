# Brief for the sealed H4 session (design 5.3)

You write one attack family, H4, for a simulated verification market. You work alone, in your own clone of the repository at the tag `h4-base`. Nobody in the project reads your family until the evaluation report; write it so it stands on its own.

## What you may read

- The family interface: `sim/policies/families.py` (`Family`: a name, the knob names in coordinate order, bounds for the bounded knobs, and a factory that turns a knob dictionary into a policy).
- What a policy observes: `sim/policies/base.py` (`ProviderView`: its own history across identities, the round, its own parameters, and an identity token usable only for equality).
- The admissible class of rules (`docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md`, section 4.0), so you know what the rules can and cannot do.
- The public constants (design 5.1): your family is built with the rule's horizon `T` and ban length `L`, and may use only these two, the provider view, and its own knobs.

Do not read `sealed/`, `sealed2/` of any other clone, the rule implementations under `sim/mechanisms/`, or the existing attack families beyond the interface above. Do not call any paid API.

## What you write

`sealed2/h4/family.py`, exporting exactly:

- `make_family(T: int, L: int) -> Family`, returning a `Family` named `"H4"` whose knob `clip` is the last knob and binary (absent from `bounds`); every other knob either has bounds `(lo, hi)` with `lo < hi` or is listed in `BINARY`.
- `BINARY: tuple[str, ...]`, the names of the binary knobs, `"clip"` included.

`sealed2/h4/containment.md`: a short note saying which existing families, if any, your family contains as special cases, and how (the knob values that reproduce them).

## How you check it

```bash
uv run python scripts/h4_check.py --bundle sealed2
```

It imports your family at two constant pairs, runs a search against two rules on the development instances, writes `sealed2/h4/check.json` last, and prints the bundle hash. A non-zero exit means the load check failed: fix the family and run it again.

## How you finish

```bash
git add sealed2 && git commit -m "H4 bundle"
git rev-parse HEAD
uv run python -c "from sim.h4_loader import bundle_sha; print(bundle_sha('sealed2'))"
```

Print the commit hash and the bundle hash as your last message. Do not push.
