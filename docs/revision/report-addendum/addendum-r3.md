# Protocol v2 report: addendum (Operation 8, review round 1)

This addendum accompanies `report.md` and `report.json`, which `scripts/report_v2.py` at tag protocol-v2 wrote. It changes no estimate and no decision.

## Interval and decision labels
- Q1 decisions: Holm over the two tests on calibrated two-sided p-values.
- Q1 intervals: calibrated Bonferroni simultaneous intervals (one-sided tails kappa x 0.05 / 4), reported beside the Holm decisions and separate from them.
- Q1 efficiency condition: descriptive: nominal one-sided 97.5 percent bounds on the paired gross-efficiency difference against -0.01; not calibrated.
- Q1 per-market and headline rows: descriptive, nominal 95 percent, unadjusted.
- Q2: descriptive, nominal 95 percent, unadjusted.
- Q3: descriptive, nominal 95 percent, unadjusted; G_min bounds are simultaneous over the c members, each member bound at tail 0.05/c.
- Q4: intersection-union per market, Holm over six markets (a missing market counts p = 1); bounds are calibrated one-sided at tail kappa x 0.05 / 6.

## Claim scope
All claims are conditional on the six sampled markets, the stated neighbourhood, the fixed pair (Q1, Q2, Q4), the searched families, and the frozen searches. Q4 replicates the B3 - R3 comparison under D2+H3 and R3's efficiency condition, not the complete amended PASS predicate of the first evaluation. Multiplicity is controlled within Q1 and within Q4 separately; there is no paper-wide 5 percent familywise guarantee. "Confirmatory" means specified before the fresh draw; it does not mean exact nominal error control on the fresh, selected-policy distributions. Q4 is an internal replication on fresh instances, not an independent-team replication. (Design 9.4.)

## Deviations from the protocol

1. Fresh-market configurations. The pods (Linux x86) recalibrated each fresh market; `instances.json` holds the arm64 calibration. The report used the configurations a Linux container reproduces (`results/v2/deviation/instances_container_configs.json`); the headline market uses the registered ones.

| market | registered config hash | reproduced config hash | pod hashes match | differing values | max ulps | verify |
|---|---|---|---|---|---|---|
| fresh0 | a756dbc6c75b3cbe2fd9750b7eb4b0f016c1b5c18736c0c09866c3cb99cbfe58 | 65b364cea67db322d69f6c907d622c898e43166480267b3e761ed3ba2c580315 | True | 2 | 1 | ok |
| fresh1 | ea43dd87f879d881fdc925402df633fb71f565418e74080a16ad3a4bb40c3724 | 44b4fc926421c5750356de965bb1160b7c35cf72dc41a4b40df4dad9883a8ba9 | True | 2 | 1 | ok |
| fresh2 | 1c0ab9b255cd54ffb175cdaaa703aae65c41478fe20170c5914564e2322f98ad | 3e40be96cf9e1fb8c8f5c71375dc333338591805677145e21aa81f612ca7d8c8 | True | 6 | 1 | ok |
| fresh3 | e02867f81ee4783f9d85fb8e7aa8b9a28fa513ccf62179bd60caaad5681fabeb | f5c1cd00ec2f0a85aca0e42efa102f5c0a6dcfbb0c9b349c8a2861816b0e961b | True | 4 | 1 | ok |
| fresh4 | 3b8eab881fe3ba1b8f2ddf8d7b60d7f0cdf4aa7036d7ae8cc07b5a8787b415b4 | 112608c64b4c1b8558985dd951b6bd6b614fc5618d4da93e03b0642e94344d82 | True | 2 | 1 | ok |
| fresh5 | cfa2b612da5de7e4878e984428ce73b0a4054deb380e42a0b53b5783dc55f2bf | bf562902ff492ab31c992c537d4e89c841e157e4b9f09bb83c217948fc81038d | True | 1 | 1 | ok |

Evidence: `results/v2/deviation/cfg_ulp_all.json` (sha256 e41a598f01f279e79a5a47ad1114c1d3650b051da053a6fbfea6fc5bfe6ef07e), written by `docs/revision/deviation/cfg_ulp.py`. These checks establish matching pod hashes, differences within one unit in the last place, and verification with the reproduced configurations; they do not show that the decisions are unchanged, since small input differences can change discrete simulation branches. A re-evaluation of the frozen policies of the 36 fresh-market cells that Q1 and Q4 use, on the registration platform with the registered configurations (`results/v2/deviation/stability.json`, sha256 ebbde40a4aeb6e583a05aaef0fa5da89f21c73faa116d70fdb5a6490c0ca3eea), changes per-seed gains in 36 cells and cell means by at most 0.0074; every Q1 and Q4 decision is unchanged.

2. Evaluation cap. The author raised the evaluation cap from 40 to 43 USD after the first fresh pods cost about ten percent more than estimated (recorded approval: "Raise caps, start fresh5 now: evaluation cap 43 USD, program limit 55 USD (development cap 12 USD unchanged), Ömer Demirel, 2026-11-04, chosen in the Claude Code session after the wave-1 overrun (fresh pods 4.65-4.80 USD against 4.26)."). Evaluation spend: 39.449 USD. No analysis changed.

## Search-flag dependencies

Design 6.5 labels a confirmatory decision that uses a search-flagged cell as a decision about the prescribed search procedure. A cell's reference is built from the search records of every family on its menu and, for fixed rules, from other rules' searches (the bank), so a decision can use a flagged cell's search through its references. Traced through the upstream links of the evaluate, reference, search and bank records (freeze records excluded):

- Q1 C*-F111|D2+H3: already labelled in the report (depends on fresh0@rho0.2|C*|D2+H3|profit, fresh1@rho0.2|C*|D2+H3|profit, fresh1@rho0.2|F111|D2+H3|profit, fresh3@rho0.2|C*|D2+H3|profit, fresh4@rho0.2|F111|D2+H3|profit)
- Q1 C*-F111|X7-SC: newly qualified: about the prescribed search procedure (depends on fresh0@rho0.2|C*|D2+H3|profit, fresh1@rho0.2|C*|D2+H3|profit, fresh1@rho0.2|F111|D2+H3|profit, fresh3@rho0.2|C*|D2+H3|profit, fresh4@rho0.2|F111|D2+H3|profit)
- Q4 fresh0: newly qualified: about the prescribed search procedure (depends on fresh0@rho0.2|C*|D2+H3|profit)
- Q4 fresh1: already labelled in the report (depends on fresh1@rho0.2|C*|D2+H3|profit, fresh1@rho0.2|F111|D2+H3|profit)
- Q4 fresh2: no flagged dependency
- Q4 fresh3: newly qualified: about the prescribed search procedure (depends on fresh3@rho0.2|C*|D2+H3|profit)
- Q4 fresh4: already labelled in the report (depends on fresh4@rho0.2|F111|D2+H3|profit)
- Q4 fresh5: no flagged dependency

## Q1 side fields per market (descriptive, means, F111 minus C*)
- fresh0 C*-F111|D2+H3: gross_eff_diff 0.0009; net_eff_diff 0.0009; ref_profit_diff 0.2186; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0001
- fresh0 C*-F111|X7-SC: gross_eff_diff 0.0009; net_eff_diff 0.0009; ref_profit_diff 0.2186; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0001
- fresh1 C*-F111|D2+H3: gross_eff_diff 0.0013; net_eff_diff 0.0013; ref_profit_diff 0.0204; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0004; served_share_diff 0.0000
- fresh1 C*-F111|X7-SC: gross_eff_diff 0.0013; net_eff_diff 0.0013; ref_profit_diff 0.0204; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0004; served_share_diff 0.0000
- fresh2 C*-F111|D2+H3: gross_eff_diff 0.0030; net_eff_diff 0.0030; ref_profit_diff 0.3009; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0011
- fresh2 C*-F111|X7-SC: gross_eff_diff 0.0030; net_eff_diff 0.0030; ref_profit_diff 0.3009; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0011
- fresh3 C*-F111|D2+H3: gross_eff_diff 0.0020; net_eff_diff 0.0020; ref_profit_diff 0.2054; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0000
- fresh3 C*-F111|X7-SC: gross_eff_diff -0.0003; net_eff_diff -0.0003; ref_profit_diff 0.2054; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff 0.0000; served_share_diff 0.0000
- fresh4 C*-F111|D2+H3: gross_eff_diff -0.0025; net_eff_diff -0.0025; ref_profit_diff 4.6513; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0001; served_share_diff 0.0005
- fresh4 C*-F111|X7-SC: gross_eff_diff 0.0000; net_eff_diff 0.0002; ref_profit_diff 4.6513; audit_spend_diff -0.0002; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0001; served_share_diff -0.0001
- fresh5 C*-F111|D2+H3: gross_eff_diff 0.0005; net_eff_diff 0.0005; ref_profit_diff 0.7191; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0001; served_share_diff -0.0000
- fresh5 C*-F111|X7-SC: gross_eff_diff 0.0005; net_eff_diff 0.0005; ref_profit_diff 0.7191; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0001; served_share_diff -0.0000
- headline C*-F111|D2+H3: gross_eff_diff 0.0008; net_eff_diff 0.0008; ref_profit_diff -0.2219; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0000
- headline C*-F111|X7-SC: gross_eff_diff 0.0008; net_eff_diff 0.0008; ref_profit_diff -0.2219; audit_spend_diff 0.0000; false_refund_focal_diff 0.0000; false_refund_others_diff -0.0002; served_share_diff 0.0000
