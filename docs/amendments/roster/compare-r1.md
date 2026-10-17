# Round 1 comparison (lead's matrix)

Agreements (both seats, independently):
- Q1: the locked claim is not demonstrably impossible but has a poor prospect; the obstacle is the baseline clause; random-audit dominance is a live kill outcome. Corrections to the lead: B2's registered headline position is high (gain -0.007, loss -0.001), not median; H2 containment is not established by the public spec; the loss alternative can pass through negative R* loss; the lead's beta example (0.087 gain, 0.027 loss) is beta 0.01, not 0.02.
- Q2: both recommend (e): keep the H2 absolute requirements (eff >= 0.90, gain <= 0.30, budget) at beta 0.05, add the same absolute requirements on H3, and add a comparative H3 clause: paired lower-98.75% bound of gain(B, H3) - gain(R*, H3) >= 0.10 for each of B2 and B3; new signed tag, amendment note, public timestamp; sealed bundle unchanged; publish the original predicate's verdict too; the new paired statistic needs its own coverage validation; disclose that the design memos preceded the amendment; freeze the amendment before implementation or tuning.
- Q3: rank 1 = B3's second-score allocation and payment + B2's spread audit count + audit selection "newest identities first" (first-observed round, ties by the audit keys) + full refund + ban, no hold-back; rank 2 = B2's tiers with the same audit selection. Bonds deferred (cannot bind a fresh identity before receipts). Baseline logic must be reimplemented inside proposed.py.
- Q4: same five tests in substance; same exploitation risks (small inflation below tol, bid manipulation, late-episode cheating, multiple simultaneous entrants, predictable audit priority).

Conflicts / open:
- C1 tuning grid: Sol tol x L = 9 x 9 = 162; Astra 3 x 3 = 9 (tol {0.12, 0.14, 0.16}, L {3, 10, 20}); Astra's design 2 uses 27 x 3 x 3 = 243.
- C2 validation of the new paired-gain endpoint: both require it, neither gives the procedure or its cost.
- C3 newest-first auditing vs alternatives (fewest audits per served job; partial randomization) against multiple entrants and predictability.
- C4 late-episode cheating: both flag; neither proposes a schedule.
- C5 Astra: first-observed round must not reset after a ban; Sol silent.
