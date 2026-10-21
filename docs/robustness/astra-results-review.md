VERDICT: reject

CORRECTIONS:

1. Replace section 4’s first two sentences with: “27 of 30 fixed doubling checks change dev-train gain by less than 0.005. Three exceed this threshold: R3 sigma 0.025 (+0.050995), R3 J60 (+0.017527), and B3 sigma 0.10 (+0.005192), all under D2+H3.” Add: “These searches remain incomplete; their reported dev-val means are attack estimates, not certified population lower bounds. Dev-train improvements cannot be added to dev-val means.”

2. In section 1, label J60’s R3 value `0.000 (search incomplete; doubling +0.018 on dev-train)`. Add the same dev-train qualification to the sigma 0.025 annotation. In section 3, replace “J60 (0.000) strengthened as predicted” with “J60’s original estimate was lower, but its doubling check found a further attack improvement.”

3. Replace section 2.2’s “Gains are near zero because shading is detected readily” with: “D2 gains are zero for all three audited rules. Under D2+H3, B2 retains gain 0.200; B3 gives −0.008 and R3 gives 0.000.” In the noise prediction row, state that sigma 0.025 raised D2 gains for **all three** audited rules: B2 0.033, B3 0.067, R3 0.067.

4. Replace the Positions outcome with: “Held at the headline budget, but not throughout the budget grid. At beta 0.10, low-position gains are B2 0.000, B3 0.014, R3 0.019; high-position gains are B2 0.000, B3 0.057, R3 0.040.” Add to Budget: “The prediction that D2 gains fall with beta fails for B2 at the median: −0.000253, 0.003774, 0.000000.”

5. Replace “rho 0.05 held for H3” with: “The predicted near-zero H3 gain was not established: R3 gives 0.067, close to its headline 0.070 and equal to B3.” Replace “X5 … at the low end” with “X5 gives 0.046948, below the predicted 0.05–0.10 range.” Replace the Horizon outcome with: “Mixed: T100 moves against the prediction; T400 moves in the predicted direction; statistical support for either difference is not established.” Score X3 separately: its selected window avoids terminal rounds, as predicted.

6. In section 2.3, replace “the synchronised and staggered profiles coincide” with “their focal mean gains coincide; other diagnostics differ.” Identify B2 0.543 as staggered; synchronised B2 is 0.541. Replace the matched-control sentence with: “The report omits matched-control outputs; the stated −0.028 and −0.068 require a separate cited artifact.” Replace the final sentence with: “At c 5, fresh demand exceeds audits in 178.2 rounds on average and focal fresh coverage is 0.392, consistent with overload; these data do not isolate timing as the cause.”

7. Add to Fresh congestion: “The predicted lower staggered gains do not occur in the selected R3 results. The predicted independence of B2/B3 gains from c also fails descriptively: synchronised B2 gives 0.580/0.586/0.541 and B3 gives 0.357/0.298/0.430.”

8. Add to section 4: “Nine twin-versus-honest checks fail: B2 at the high position, across all three budgets and core families.” Add a Diagnostics outcome: “The checks support high replacement audit rates; bound (5) holds in 63/64 admitted seeds. Identity (4) uses measured cycle components, so agreement is not an independent forecast.”

9. In section 5, replace the claim of an advantage across positions and disappearance “exactly where the theory says” with: “Selected attacks show lower R3 gains in many tested variants, subject to the stated exceptions and incomplete searches. At eta 10, selected audited-rule attacks do not reset; residual gains remain. Corollary 1 concerns free replacement, and the renewal theorem does not cover adaptive D2+H3 or coalitions.”

REASON: All 52 numerical entries in the main table match the report at the stated precision. The rho = 1 explanation matches calibration and code: allowance 500 equals the terminal reserve, which leaves zero early quota. The doubling count is wrong, several predictions are scored too generously, and the X6 interpretation exceeds the supplied evidence. The exploratory, dev-val, and parameter-transfer disclosures are appropriate. Pod counts, elapsed compute, and cost are not verifiable from the supplied report.

CONFIDENCE: 0.98
