VERDICT: reject

CORRECTIONS:

1. In the abstract and introduction, replace “cannot take collateral” and “cannot demand a bond” with: “We restrict the mechanism class to exclude entry fees, identity certification, and collateral before receipts.” These are model restrictions, not established limits of compute markets.

2. Replace “uniform random auditing cannot use exclusion at all” with: “With immediate free replacement and identity-independent allocation, prices, and audit selection, a ban adds no continuation loss; escrow refunds still apply.”

3. Replace both descriptions of unconditional newcomer auditing with: “R3 gives priority to jobs from identities within their first L rounds. It audits all such jobs only when the round’s quota covers fresh demand. It divides residual audits between newest-first targeting and uniform selection.”

4. Replace the protocol’s broad chronology claim with: “The original protocol was locked before proposed-rule implementation. Design reasoning preceded amendments 1 and 2. After a development test killed the first rule, amendment 3 registered one successor before its implementation.” Add: “H2 was written in a separate session; its containment of D2 was disclosed before unsealing.” Replace “every later change” with “the four documented amendments.” Signing records changes; it does not remove adaptation to observed results.

5. Replace the amended-result sentence in both locations with: “The amended predicate passes on public H3 at beta 0.05 and the median position, using 40 fresh seeds. Mean normalized gains are 0.570, 0.353, and 0.071 for B2, B3, and R3. R3’s mean gross efficiency is 0.999; its lower bound is 0.9980. Interval admission used development distributions with B3 as a proxy, and does not establish nominal coverage for selected R3.” Define gain using the registered reference and per-provider first-best surplus. Delete “cheaters keep … a fair provider’s surplus.”

6. Replace “the proposed rule is safe” with “R3 passes the registered H2 rule clause.” Add to the introduction: “The main benchmark measures unilateral deviations against honest-max opponents. It establishes neither equilibrium nor incentive compatibility.”

7. Replace “A renewal-reward analysis explains the gap and is confirmed by 72 … configurations” with: “A conditional renewal analysis describes stationary reset policies, excluding adaptive D2+H3 and coalitions. Seventy-two exploratory configurations use development-validation seeds. The renewal identity checks accounting with measured cycle components; it is not an independent forecast. The surplus bound holds empirically in 63 of 64 admitted seeds.” Restrict the shading proposition to served providers, zero continuation loss, and the locked parameters.

8. Replace the abstract’s robustness conclusion and introduction result (iv) with: “The 292 pre-stated exploratory search cells reuse development-validation seeds. Selected attacks show lower R3 gains in many variants, with exceptions and incomplete searches. High audit cost exhausts the early quota; high noise reduces efficiency; coalition demand overloads newcomer coverage. The coalition results do not isolate simultaneous timing as the cause.” Do not describe thirteen variants as thirteen successes.

9. Replace the novelty sentence with: “We study newcomer-priority auditing in a repeated procurement model with noisy verification, escrow-capped sanctions, and free identity replacement, and report a prospectively registered evaluation with disclosed amendments.” Replace “complete public record” with “documented study record” until public artifact availability is verified. Sarmenta already studies spot-checking, newcomer credibility, and identity replacement; distinguish that work explicitly. [Primary paper](https://groups.csail.mit.edu/cag/bayanihan/papers/ccgrid01/ccgrid01.pdf).

10. In the outline, add to Results: “Enforcement-matched ablations; gain decomposition; gross versus net efficiency; search failures and twin-reference failures.” Add to the H1 subsection: “Exploratory; R3 INCONCLUSIVE because its audit rule is not expressible; final cell completed after an outcome-informed cap amendment.” Move detailed hashes, review histories, and diagnostic tables to supplementary material. Replace “8 pages plus appendices” with “8 main pages containing essential evidence; extended proofs and records in supplementary material.” [AAMAS guidance](https://warwick.ac.uk/fac/sci/dcs/aamas2027/guidelines-and-policies/qa/).

ANSWERS:

(1) No. The draft reports the original failure correctly, but overstates newcomer coverage, theory validation, robustness, and the amended PASS. It also confuses an efficiency bound with a mean. The missing qualifiers affect the central claims.

(2) A narrow contribution is defensible. Broad novelty for verification as newcomer dues is not established. Separate the specific procurement mechanism and its evaluation from earlier credibility-based verification. “We are not aware” does not resolve this gap.

(3) The section plan is workable after correction 10. Keep the theorem’s assumptions, principal counterexamples, and statistical limitations in the main paper. Reduce procedural history before cutting evidence that tests the mechanism.

(4) Use “Audit Dues: Newcomer-Priority Verification under Free Identity Replacement.” It identifies the mechanism without making registration the main contribution.

(5) AAMAS is a plausible fit for an empirical mechanism paper; EC would need a stronger general theoretical contribution. However, AAMAS 2027’s main-track deadline was 8 October 2026, before this draft. Select a later submission opportunity. [Official call](https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-main-track/).

CONFIDENCE: 0.94
