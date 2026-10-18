# Deep research brief: audited compute markets with cheap identities

Purpose: find the closest formal models, known results, and practical systems for the problem below, so that a paper can position its contribution correctly, cite the right prior work, and avoid claims the literature already settles. The brief states the problem exactly as our simulator implements it, what we have measured, and the questions we want answered.

## 1. The problem in one paragraph

A trusted operator runs a market for compute jobs. Each round, buyers post jobs with values and providers post offers: a claimed quality and a price. Quality is not observable at delivery; the operator can audit a delivered job at a fixed cost, from a fixed total audit budget that covers only a fraction of served jobs. A provider who delivers less than claimed earns the price for less effort. A caught provider can be refunded against, banned for a while, or (within a cap) lose a small bond, but nothing worse: the operator cannot fine beyond escrow and cannot refuse re-entry, because identities are cheap: a provider can drop a burned identity and return under a fresh one at zero or small cost. The question is which market rule (allocation, pricing, audit selection, enforcement) keeps lying unprofitable, keeps honest providers well served, and does so with the small audit budget, under adaptive cheating strategies and under identity replacement. We compare a proposed rule against two standard rules and test it with a pre-registered, falsification-first protocol.

## 2. Formal setting (as implemented)

Time. Discrete rounds t = 1..T, T = 200.

Jobs. J = 50 unit jobs per round. Job j has value v_j drawn i.i.d. uniform on [0.6, 1.4]. Buyer value for delivered quality y is v_j * y. Buyers are passive and truthful; a buyer accepts an offer only if the claimed value covers the price.

Providers. N = 10 entities. Entity i has a quality ceiling q_max_i in (0, 1] (grid 0.60 to 1.00), a per-job cost a_i + b_i * q for effort q (a_i = 0.02, b_i from 0.40 down to 0.22), a capacity k_i = 6 jobs per round, and an outside option of zero. An entity may drop its identity and re-enter under a fresh one at entry cost e (default 0); the operator sees only opaque identity tokens and must be invariant to relabeling them.

Delivery. A served job yields y = q + eps, eps ~ N(0, sigma^2), sigma = 0.05. Cost is paid per job served.

Claims. A claim c in [0, 1] promises expected quality at least c. Truthful iff c <= q (the effort chosen that round). Inflation is c - q > 0. Rules differ in how they audit and enforce the promise, never in what it means.

Round order. Jobs drawn; each active provider privately chooses effort and posts (claim, bid) or abstains; the rule allocates jobs; the rule prices them and buyers fund escrow; delivery; the rule picks jobs to audit within budget (an audit reveals y exactly at cost alpha); the rule enforces; escrow settles (refunds to buyers, the rest to providers). An exit takes effect at the start of a round: the old identity retires, the fresh one offers immediately.

Audit budget. B = beta * S_hat, where S_hat is the expected first-best surplus over T rounds; beta in {0, 0.01, 0.02, 0.05, 0.10, 0.20}, headline beta = 0.05. Audit cost alpha = rho * m with m the mean first-best surplus per served job; rho = 0.2 default (sweep {0.05, 0.2, 1}). At the headline setting the operator can audit about 2,500 of roughly 10,000 served jobs per episode, so about a quarter.

Admissible rules (locked before any rule was designed). Inputs: current offers, job values, purchased audit results, own memory, locked constants. Enforcement may only: refund up to the full escrow of an audited failed job; ban an identity for at most 50 rounds; hold back at most 3 rounds of an identity's net receipts as a bond with a stated forfeit schedule; and use allocation priority and audit selection. No fees, no fines beyond escrow and bond, no consequences for unaudited jobs, no operator money injection. Audit spend never exceeds B.

Baselines (tuned pre-lock on a registered grid). B1: posted tier prices by claim band, no audits. B2: B1 plus uniform random audits spread evenly over rounds, refund plus ban L on failure. B3: a descending-value sequential second-score auction (score = v_j * c - bid; the winner is paid value times claim minus the runner-up score; Che 1993 style) plus the same random audits and enforcement. Tuned values: B2 prices (0.187, 0.374, 0.534), tolerance 0.12, ban 10; B3 tolerance 0.12, ban 10.

Attackers. One focal provider deviates; all others play honest-max (full effort, truthful claim, cost-based bid). Development families: D1 (fixed cheat: effort fraction, claim markup, margin, bid markup), D2 (adaptive cheat: markup decays after a failed audit and recovers otherwise). Each family is searched by CMA-ES (5 restarts x 300 evaluations, 5 training seeds) for the knobs that maximise the focal provider's profit under the rule; the result is evaluated on 20 fresh seeds. H3 (public stress test): any D2 policy wrapped with identity replacement: exit the round after a failed audit and re-enter fresh. H2: a sealed attacker family written by a separate party and unseen until the final evaluation. H1: an LLM provider with a sealed prompt.

Metrics (per seed, then mean with a paired bootstrap bound). S*: first-best surplus (max-weight assignment with full effort). Gain = (pi_attack - pi_reference) / (S* / N), where the reference is the best truthful policy for that provider (its own matched truthful twin, honest-max, or abstention). Gross efficiency = (net surplus + audit cost) / S* with true quantities. Harm to others. Audit spend. Honest false-failure rate Phi(-tol / sigma).

The registered claim (decided after the freeze on sealed H2 and 40 fresh seeds, beta = 0.05). Rule clause: gross efficiency at least 0.90 and gain at most 0.30 (lower and upper 95 percent bounds), audits within budget. Baseline clause (original lock): for each of B2 and B3, either gain at least 1.0 or an inflation-caused efficiency loss at least 0.05 above the proposed rule's; judged practically unwinnable from development data and reported anyway. Amended clause (registered before the rule was designed): on H3, the proposed rule within the same absolute limits, and its gain at least 0.10 below B2's and below B3's, paired per seed, 98.75 percent lower bounds. H1 is exploratory.

## 3. The proposed rule (R3, after one registered repair)

Allocation and pricing: B3's second-score auction. Audit count: a terminal reserve of min(J * L, budget) audits for the last L rounds, where every served job is audited while audits remain; before that, a cumulative linear quota per round with carry-over of unspent audits. Audit selection within a round: (1) priority phase: every served job of an identity younger than L rounds, newest identity first, then by a per-job random key, up to the round's quota; (2) the remainder is split: half targeted (T1: newest identity first; T2: lowest audits-per-served-job), half uniform at random. Enforcement: full refund of the failed job's escrow and a ban of L rounds; no bond. Tuned on the registered grid: tolerance 0.16, L = 10. The audit selection cannot be stated in the fixed vocabulary our comprehension test uses, which is why H1 stays inconclusive for it.

## 4. What we have measured (development data, 20 evaluation seeds, beta = 0.05)

- Against searched D2 attackers: B1 gain 0.41; B2 0.005; B3 0.044; R3 0.041 at gross efficiency 0.995. Random audits at a quarter coverage already deter the development families.
- Against identity replacement (H3): B2 gain 0.58, B3 0.36, R3 0.07 at efficiency 0.998. Identity hopping is where the baselines break: with about 180 to 200 replacements per episode, a cheater burns identities faster than random audits catch it.
- All-honest run under R3 on the 20 dev-val seeds: gross efficiency 0.997; 50,000 audited jobs in total (2,500 per seed); 28 failed audits against 34.4 expected from Gaussian delivery noise (Phi(-0.16/0.05) = 6.9e-4 per audited job, so 1.7 per seed); 28 ban events against 34.3 expected.
- The first version of R3 split the round quota in halves and could not fully audit a six-job entrant when the round held 10 audits; that arithmetic failure was predicted in the registration, measured, reported as a kill, and repaired by one disclosed amendment (the priority phase).
- Costs: about 2,500 audits per episode at alpha about 0.2 of the surplus per job, which is roughly 5 percent of first-best surplus.

## 5. Questions for the deep research

A. Costly verification and audit allocation.
1. What is the closest formal model: a principal allocates goods or payments to agents on reported types, can verify reports at a cost, with capped punishments (refund of the payment, temporary exclusion)? Candidates: costly state verification (Townsend 1979; Gale and Hellwig 1985), optimal allocation with costly verification (Ben-Porath, Dekel, Lipman 2014), ex post verification with limited penalties (Mylovanov and Zapechelnyuk 2017), Erlanson and Kleiner on collective decisions with costly verification, Li on costly verification with limited punishments. What do their optimal mechanisms look like, and do they favour "check the new or unknown agents first"?
2. Budgeted auditing: tax audits and compliance (Reinganum and Wilde 1985; Border and Sobel 1987; Mookherjee and Png 1989): when is uniform random auditing optimal, and when does targeting dominate? Any results on auditing under a hard budget per period with carry-over?
3. Deterrence arithmetic: results relating the audit probability, the capped penalty, and the gain from cheating (Becker 1968; Shapiro and Stiglitz 1984 efficiency wages with monitoring and dismissal). Does anything bound the minimum audit fraction needed when the penalty is capped at the job's payment plus a finite exclusion?

B. Inspection and security games.
4. Inspection games (Avenhaus, von Stengel) and Stackelberg security games (Tambe and coauthors): a defender with limited inspections against an adaptive adversary. Is a mixture of targeted and randomised inspection known to be optimal or near-optimal, and under what information structure? Are there results on sequential (round-by-round) inspection budgets with reserves?

C. Cheap identities.
5. Friedman and Resnick (2001) "the social cost of cheap pseudonyms": newcomers must pay dues; what mechanisms do they and later work propose (entry fees, initial distrust, reputation bonds), and what efficiency loss do they prove is unavoidable with free pseudonyms? Whitewashing in peer-to-peer systems (Feldman, Papadimitriou, Chuang, Stoica 2006). Sybil-proof and false-name-proof mechanisms (Yokoo, Sakurai, Matsubara; Conitzer; Cheng and Friedman 2005). Is "audit newcomers first" a known device, and is there an impossibility result when entry is free and penalties are capped at the current payment?
6. Any model where exclusion (ban) is the only lasting punishment and identities are replaceable at a cost e: how does the deterrence depend on e, the ban length, and the audit rate?

D. Procurement with unobservable quality.
7. Scoring and multidimensional auctions (Che 1993; Asker and Cantillon) with moral hazard in quality after award. Does the literature combine a scoring auction with audits and penalties, and what does it say about the second-score payment's robustness to inflated claims?

E. Repeated games with imperfect monitoring.
8. Relational contracts and imperfect public monitoring (Green and Porter; Abreu, Pearce, Stacchetti; Levin 2003): punishment phases triggered by noisy signals. Our ban after a noisy audit is such a trigger; the false-failure rate Phi(-tol / sigma) is the price. Any results on optimal tolerance (trigger threshold) when the signal is Gaussian and the punishment is a finite exclusion?

F. Outsourced computation and real compute markets.
9. Rational outsourced computation with audits and bounties (Belenkiy, Chase, Erway, Jannotti, Kupcu, Lysyanskaya 2008), rational proofs (Azar and Micali), Truebit's verification game with forced errors, Golem, iExec, Akash, Bittensor style validation. What do deployed or proposed compute markets actually do about unverifiable quality: re-execution, redundancy, reputation, staking and slashing, SLAs? What fraction of work do they verify, and what do they assume about identity?
10. Verifiable computation (SNARKs, proofs of correct execution): when the job's output is a deterministic function of the input, proofs replace audits. Which classes of compute jobs are not covered (quality as a continuous, noisy, or subjective quantity; model training quality; probabilistic outputs), so that auditing remains necessary?

G. Evaluation methodology.
11. Pre-registered or falsification-first evaluation of mechanisms against adaptive adversaries: is there precedent in economics, security, or machine learning for registering a mechanism's design and tests before the mechanism exists, sealing an attacker, and timestamping the commitments? Related: adversarial robustness evaluation protocols, red-team benchmarks with held-out attacks, pre-registration in experimental economics.
12. Empirical mechanism design with simulated or searched best responses (Vorobeychik and Wellman's empirical game-theoretic analysis; automated mechanism design): how do they handle the fact that a search finds a local best response, and what do they report as evidence of robustness?

I. Scheduling with selfish machines and mechanisms with verification (algorithmic mechanism design).
14. Nisan and Ronen's task scheduling on unrelated machines introduced mechanisms with verification: the mechanism observes a task's true execution time after the fact and can withhold payment from a machine that lied. Later work (Auletta, De Prisco, Penna, Persiano; Penna and Ventre; "ex post verifiable types") characterises what verification buys. These assume verification is free, exact, and applied to every executed task. What is known when verification is a budgeted noisy sample and the punishment is capped? Is there a bridge between that literature and costly-verification economics?
15. Selfish load balancing and the price of anarchy (Koutsoupias and Papadimitriou) treat machines or jobs as strategic; dynamic load balancing with indivisible real-valued tasks treats them as cooperative. Our operator assigns indivisible jobs to capacity-limited providers whose cost and quality are private. Is there work on load balancing or scheduling with untrusted executors where a sample of results is checked?
16. Balls-into-bins and discrepancy results for random sampling: given k uniform audits among n served jobs, what is the distribution of audits per provider and the probability that a given provider's s jobs are all missed? This is the arithmetic behind our F2 kill (five targeted picks plus a uniform remainder against a six-job entrant) and behind the uniform half's coverage guarantees.

H. What would falsify our framing.
13. Any known result that a rule in our admissible class cannot deter identity-hopping cheaters below some gain floor when e = 0, or that newcomer-first auditing is dominated by a simpler scheme (for example, pay newcomers less until audited, or require a bond before the first job). We do not allow entry fees or bonds before receipts, so note which devices our class forbids and what the literature says that costs.

## 6. Deliverable wanted from the research

1. An annotated bibliography, with verified citations (venue, year, DOI where possible), grouped by the sections above, each entry with two or three sentences on the model, the main result, and how its assumptions differ from ours (observable quality, unlimited fines, no identity replacement, static versus repeated, one agent versus many).
2. A table: our assumption versus the closest paper's assumption, for audit cost structure, penalty caps, identity cost, information available to the operator, attacker adaptivity, and the evaluation method.
3. The three or four theorems or impossibility results most relevant to a capped-penalty, cheap-identity market, with their exact conditions.
4. A short list of claims we should not make because the literature already contains them, and a short list of gaps we can legitimately claim to fill.
5. What deployed compute or data marketplaces actually do about unverifiable quality, with sources.
