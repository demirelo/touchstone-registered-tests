# Deep research prompt (paste this, and attach or paste the brief `2026-10-18-deep-research-brief.md`)

You are a research analyst with a background in economic theory (mechanism design, contract theory, repeated games), computer security (adversarial evaluation, inspection games), operations research, and distributed systems. Your task is a literature and practice survey for the problem in the attached brief: a market where an operator buys compute jobs from providers whose delivered quality is unobservable except through costly audits from a small budget, where punishments are capped (refund of the job's payment, a temporary ban, a small bond), and where a provider can abandon a burned identity and re-enter fresh. We compare an audit-selection rule that audits newcomers first and then splits the remaining audits between targeted and random picks, against random auditing, under adaptive cheating strategies, with a pre-registered, falsification-first evaluation.

## What I need

Find the closest formal models, the known optimal or impossibility results, the standard evaluation methods, and what deployed systems do. Then tell me which of our claims the literature already contains, which assumptions in our model the literature would challenge, and where a real gap is.

## Search by concept, not by our words

Our vocabulary is one of many. The same problem appears in several fields under different names. For each concept below, search the alternative vocabularies and any others you find; include a result when the mathematical structure matches, even if the application is far from compute markets.

1. Unobservable quality verified by costly audits of a sample. Alternative names: costly state verification; costly verification mechanisms; ex post verification with limited penalties; claims auditing in insurance; tax audit selection and compliance; acceptance sampling and quality inspection in manufacturing (lot inspection, skip-lot sampling); customs and food-safety inspection; click-fraud and ad-fraud sampling audits; gold-standard or honeypot tasks in crowdsourcing; spot checks; proctoring; monitoring in agency theory; moral hazard with monitoring; efficiency wages with random monitoring and dismissal; deterrence (Becker).
2. Limited inspections against an adaptive opponent. Alternative names: inspection games; security games; Stackelberg security games; patrol and screening allocation; attacker-defender games; randomized auditing; strategic auditing; audit games (Blocki, Christin, Datta, Procaccia, Sinha); moving-target defense; adversarial classification and evasion.
3. Cheap or free identities. Alternative names: cheap pseudonyms; whitewashing; Sybil attacks; false-name-proofness; identity churn; reputation systems with newcomers; entry fees versus initial distrust; pay-your-dues; reputation bonds; collateral and slashing; exclusion as punishment; re-entry after punishment; relational contracts with exit.
4. Temporary exclusion triggered by a noisy signal. Alternative names: imperfect public monitoring; trigger strategies; punishment phases; relational contracts; statistical process control with false alarms; type I and type II error trade-off in enforcement; tolerance or threshold setting under Gaussian noise; grim trigger versus finite punishment.
5. Procurement where the winner can under-deliver. Alternative names: scoring auctions; multidimensional auctions; second-score auction; procurement with moral hazard; quality shading after award; contract enforcement in public procurement; service-level agreements and penalties; performance-based contracting.
6. Markets or platforms for computation and data where output quality is hard to verify. Alternative names: outsourced computation; verifiable computation; rational proofs; verification games; redundancy and re-execution; proof of useful work; decentralized compute marketplaces (Golem, iExec, Akash, Render, Bittensor and similar); cloud SLAs; machine learning marketplaces; data marketplaces; crowdsourcing quality control; federated learning with unreliable participants; peer prediction and truthful reporting without verification.
7. Evaluating a mechanism against adversaries you did not design. Alternative names: empirical mechanism design; empirical game-theoretic analysis; automated mechanism design; red teaming; adversarial robustness benchmarks with held-out attacks; pre-registration in experimental economics; registered reports; sealed or escrowed test sets; falsificationist evaluation; adaptive data analysis and the garden of forking paths.
8. Budgeted sequential inspection with a reserve.
9. Scheduling and load balancing with selfish machines, and mechanisms with verification. Alternative names: algorithmic mechanism design for task scheduling (Nisan and Ronen's unrelated-machines scheduling, where the mechanism can verify a machine's true execution time after the task runs and withhold payment from liars); mechanisms with verification (Auletta, De Prisco, Penna, Persiano; Penna and Ventre on collusion-resistant mechanisms with verification; "verifiable" or "ex post verifiable" types); selfish load balancing and the price of anarchy (Koutsoupias and Papadimitriou); dynamic load balancing with untrusted or strategic processors; balls-into-bins and discrepancy bounds for randomised assignment and for randomised sampling (how evenly k uniform audits spread over providers, and the probability that a provider's jobs escape a uniform sample). Our market is a load-balancing problem with incentives: an operator assigns indivisible jobs to capacity-limited providers whose true cost and quality are private, verifies a sample after execution, and can punish only within caps. Ask specifically: what do mechanisms-with-verification results assume about the cost and reliability of verification, and what changes when verification is a budgeted noisy sample instead of free and exact.
 Alternative names: audit budget pacing; sequential allocation of inspections; secretary-type and prophet-type inspection problems; end-game effects in finite repeated games; terminal round problems; backloading of monitoring.

For every cluster (nine in all): report the two to five most relevant works, the model, the main result, and exactly how its assumptions differ from ours (observable quality, unbounded fines, no identity replacement, static versus repeated, one agent versus many, committed versus adaptive adversary).

## Specific questions to answer

- Which formal model is closest to ours, and what does its optimal mechanism look like? Does it audit unknown or new agents first?
- When is uniform random auditing optimal, and when does targeting dominate? Any results for a hard per-period budget with carry-over?
- With penalties capped at the current payment plus a finite exclusion, is there a known lower bound on the audit fraction needed to deter, as a function of the cheating gain and the entry cost of a fresh identity? Is there an impossibility result when entry is free?
- What devices does the cheap-pseudonym literature propose (entry fees, initial distrust, bonds, reputation discounting), and what is their proven efficiency cost? Our admissible class forbids fees and bonds before any receipts; say what that forbids us from doing.
- Is "mix targeted and randomized inspection" known to be optimal or near-optimal in security games, under what information structure?
- Is the finite ban after a noisy signal analysed anywhere with an explicit false-alarm rate like Phi(-tolerance / sigma), with results on the optimal tolerance?
- What do deployed compute, data, and crowdsourcing marketplaces actually do about unverifiable quality, what fraction of work do they verify, and what do they assume about identity? Cite documentation, whitepapers, or measurements.
- Which job types cannot be covered by cryptographic verifiable computation, so that audits remain necessary?
- Is there precedent for registering a mechanism's design and tests before it exists, sealing an attacker, and timestamping commitments? What do adversarial-evaluation methodologies recommend about adaptive attackers found by search rather than designed by hand?

## Rigor rules

- Every citation must be real and verifiable: give venue, year, and a DOI or stable URL; if you cannot verify a reference, say so and do not include it as a fact.
- Prefer primary sources; use surveys to find them. Mark claims that come from your own reasoning rather than a source.
- Do not restrict yourself to economics; computer science, operations research, law and economics, statistics, and practitioner documentation all count.
- Treat a match as a match when the mathematics is the same, even if the words differ; say explicitly how the mapping works (what plays the role of the audit, the penalty, the identity, the budget).
- Report disagreements between sources rather than smoothing them over.

## Output format

1. Executive summary (one page): the three closest models, the two or three results we must cite, the one or two assumptions of ours that the literature would challenge, and the gaps we can legitimately claim.
2. Annotated bibliography grouped by the eight concept clusters, each entry: citation, model in two sentences, main result, the assumption differences from ours.
3. A table mapping our assumptions to the closest paper per cluster (audit cost structure, penalty cap, identity cost, operator information, attacker adaptivity, evaluation method).
4. The most relevant theorems or impossibility results with exact conditions.
5. Claims to avoid because they already exist, and claims that would be new.
6. What deployed systems do, with sources.
7. Open questions you could not settle, and the searches you ran that returned nothing.
