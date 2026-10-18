# Falsification record of the proposed rule R3 (amendment 3; 2026-10-18, 21:55)

The amendment-2 rule's record (F2 kill) is `falsification-2026-10-18-amendment-2-kill.md`. This run: the sweep `results/sweep_proposed` rebuilt from the bank stage on for all four rules after the re-tune (baseline search records reused, hashes verified by the harness), pods 17:25 to 21:54, all deleted.

Parameters: `{"L": 10, "allocation": "A", "targeting": "T1", "tol": 0.16}`. Sweep records: `/Users/oemer.demirel/Projects/touchstone/results/sweep_proposed`. Quick mode: False.

## F1: PASS

```json
{
 "pytest": "36 passed in 2.61s",
 "module_check": []
}
```

## F2: PASS

- T1: pass; per seed (profit, applicable rounds, covered): 1000: (-22.8000, 199, True), 1001: (-22.8000, 199, True), 1002: (-22.8000, 199, True), 1003: (-22.8000, 199, True), 1004: (-22.8000, 199, True)
- T2: pass; per seed (profit, applicable rounds, covered): 1000: (-22.8000, 199, True), 1001: (-22.8000, 199, True), 1002: (-22.8000, 199, True), 1003: (-22.8000, 199, True), 1004: (-22.8000, 199, True)

## F3: PASS

```json
{
 "n": 20,
 "mean_gross_efficiency": 0.9971749715457037,
 "forecast": 0.97,
 "p": 0.0006871379379158483,
 "audited": 50000,
 "observed_failures": 28,
 "expected_failures": 34.35689689579241,
 "observed_ban_events": 28,
 "expected_ban_events": 34.336579470397155,
 "observed_lost_rounds": 251,
 "expected_lost_rounds": 305.6359953493596,
 "observed_lost_capacity": 1506.0
}
```

## F4: PASS

- D2 low: mean gain -0.0009, mean efficiency 0.9851, B3 - R* gain -0.0024 (se 0.0025), eff -0.0001 (se 0.0003), comparative fails: False
- D2 median: mean gain 0.0414, mean efficiency 0.9946, B3 - R* gain -0.0017 (se 0.0014), eff +0.0001 (se 0.0001), comparative fails: False
- D2 high: mean gain 0.0185, mean efficiency 0.9938, B3 - R* gain -0.0010 (se 0.0008), eff +0.0000 (se 0.0002), comparative fails: False
- D1 low: mean gain -0.0011, mean efficiency 0.9851
- D1 median: mean gain 0.0414, mean efficiency 0.9946
- D1 high: mean gain 0.0000, mean efficiency 0.9946

## F5: PASS

- reduction against B2: mean 0.5108, lower 0.9875 studentized bound 0.5006 (needs 0.1): pass
- reduction against B3: mean 0.2869, lower 0.9875 studentized bound 0.2828 (needs 0.1): pass
- H3 doubling delta_gain +0.00000 (needs |delta| < 0.005): pass
- f5_bank: `{"bank_hash": "91bae8312bb5841095b2f6d0b4ae43ddc3ad0c528e8d19da6ba8313142bcbc5e", "sources_sha256": "5132e4db6d1544339c22426a87e827b7620ce292ccebfa382572a6cc5052b514", "embeddings": {"D2+H3": ["embed_d2_in_h3", "embed_d2_in_h3_exit"]}}`
