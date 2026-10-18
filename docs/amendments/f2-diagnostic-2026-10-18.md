# F2 diagnostic at the prior parameters (amendment 3, 2026-10-18)

Registered gate before the re-tune: the unchanged F2 corner test (H3 full cheat, median position, beta 0.05, the 5 dev-train seeds) on R3 with the amendment-2 parameters (A, T1, tol 0.16, L 10), under both targeting variants.

```
T1 seed 1000: profit -22.8000 replacements 199 applicable 199 uncovered 0
T1 seed 1001: profit -22.8000 replacements 199 applicable 199 uncovered 0
T1 seed 1002: profit -22.8000 replacements 199 applicable 199 uncovered 0
T1 seed 1003: profit -22.8000 replacements 199 applicable 199 uncovered 0
T1 seed 1004: profit -22.8000 replacements 199 applicable 199 uncovered 0
T2 seed 1000: profit -22.8000 replacements 199 applicable 199 uncovered 0
T2 seed 1001: profit -22.8000 replacements 199 applicable 199 uncovered 0
T2 seed 1002: profit -22.8000 replacements 199 applicable 199 uncovered 0
T2 seed 1003: profit -22.8000 replacements 199 applicable 199 uncovered 0
T2 seed 1004: profit -22.8000 replacements 199 applicable 199 uncovered 0
F2 diagnostic at the prior parameters: PASS {'T1': True, 'T2': True}
```

Verdict: PASS (coverage complete in every applicable round on every seed under T1 and T2; the sustained cheater loses 22.8 per episode). The cycle proceeds to the registered re-tune. Figures: `results/f2_diagnostic_a3.json` (untracked).
