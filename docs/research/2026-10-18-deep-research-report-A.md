# Audited compute markets with cheap identities: literature and practice survey

## Executive summary

The market in the research brief combines several problems that are well studied separately but, on the literature I could verify, have not been solved together: costly verification, limited punishment, a finite inspection stock, strategically adaptive shirking, noisy evidence, post-award moral hazard, and costless or nearly costless identity replacement. The proposed R3 rule adds a particularly unusual instrument: a provider that resets its identity is not charged an entry fee or forced to post collateral, but instead enters a period of unusually intense verification. That makes **audit exposure itself function as the “dues” paid by a fresh pseudonym**. The model, admissible mechanism class, R3 rule, and development results I use below are those in the attached brief. fileciteturn0file0

### The three closest formal models

**The closest single mechanism-design paper is Yunan Li, “Mechanism Design with Costly Verification and Limited Punishments”, *Journal of Economic Theory* 186 (2020), 105000, DOI 10.1016/j.jet.2020.105000.** A principal allocates an object among privately informed agents, can inspect the eventual winner at a cost, and can punish a detected false report only to a limited degree. The optimum has two thresholds: low reports are pooled and allocated without inspection; an intermediate region allocates to the highest reporter with a positive inspection probability; and sufficiently high reports are pooled, with the selected winner inspected with certainty. With few agents the upper pooling region disappears; with many agents the two thresholds coincide into a shortlisting mechanism. citeturn13search2turn13search3

Li is very close to your *audit-cost/limited-sanction* primitives but very far from your most important dynamic feature. His agents do not erase their history and return with a fresh identity; verification perfectly establishes the hidden report; there is no Gaussian delivery noise, repeated service relationship, hard stock of inspections across periods, or strategically chosen effort after allocation. Nor does the optimal mechanism contain “audit newcomers first”: there is no newcomer state in the model. citeturn13search2turn13search0

**The closest model of the scarce intertemporal inspection resource is Bernhard von Stengel, “Recursive Inspection Games”, *Mathematics of Operations Research* 41(3) (2016), 935–952, DOI 10.1287/moor.2015.0762.** An inspector has \(m\) inspections to use over a larger \(n\)-period horizon against an inspectee that can violate strategically. The equilibrium is recursive in the remaining horizon and remaining inspections; under “inspector leadership”, commitment to a randomised inspection schedule can make the inspectee act legally while inspections remain. Unused inspections naturally remain available for later periods. citeturn13search1turn13academia48

That is much closer to your hard total audit budget than the usual static audit literature. But it has one strategic inspectee, no entry or whitewashing, no noisy quality measurement, no procurement auction, and an inspection catches a contemporaneous violation rather than sampling a noisy realisation of expected service quality. Importantly, its solution is **state-dependent randomisation over inspection time**, not a theorem supporting a deterministic linear pacing rule plus an all-audit terminal reserve. citeturn13search1

**The closest model of free identity replacement is Eric Friedman and Paul Resnick, “The Social Cost of Cheap Pseudonyms”, *Journal of Economics & Management Strategy* 10(2) (2001), 173–199, DOI 10.1111/j.1430-9134.2001.00173.x.** In a large repeated random-matching society with finite-lived participants, cheap identity changes and a small non-vanishing probability of mistakes, substantial cooperation is sustained by making newcomers “pay their dues”, meaning that new identities initially receive worse treatment. Their main result is an asymptotic bound showing that no equilibrium can sustain significantly more cooperation than their dues-paying equilibrium. They discuss entry fees, which restore trust at the cost of excluding low-value entrants, and free but unreplaceable pseudonyms as alternatives. citeturn15search1

That paper is the strongest prior-art warning against claiming that “new identities should be treated differently” is new. What appears genuinely different in R3 is **the form of the newcomer handicap**: rather than fees, degraded service or ex ante collateral, it spends scarce verification disproportionately on recent identities. I did not find a prior theorem establishing newcomer-first *inspection* as optimal.

### The results that are hardest to write around

Three citations should be central to the paper's positioning.

First, **Li 2020** already establishes that limited punishments can make optimal costly-verification mechanisms pool reports and use report-dependent, sometimes certain, inspection. Thus “limited sanctions fundamentally change optimal auditing/allocation” is prior art, not a contribution. citeturn13search2turn13search3

Second, **Friedman–Resnick 2001** already establishes that cheap pseudonyms create an unavoidable newcomer problem and that an initial handicap, “dues”, is a natural efficient response. Feldman, Papadimitriou, Chuang and Stoica later reach a closely related practical conclusion for whitewashing in peer-to-peer systems: penalising all newcomers can control whitewashing, although its welfare cost grows with legitimate turnover. citeturn15search1turn16search0turn16search11

Third, **von Stengel 2016** already treats a strategic opponent facing a finite stock of inspections over a finite horizon. Any claim that merely “a fixed inspection stock should be allocated strategically over time rather than spent mechanically” is therefore too broad. citeturn13search1

A fourth highly relevant result is Reinganum and Wilde's tax-compliance analysis. In their principal-agent tax setting, report-independent random audit rules are weakly dominated by report-contingent cutoff auditing, and under lump-sum taxes and fines cutoff rules are least-cost truth-inducing. That directly contradicts any broad claim that uniform auditing is intrinsically optimal simply because it is unpredictable. citeturn2search1turn2search4

### Where the literature would challenge the model

The strongest challenge is to **temporary exclusion as an independent sanction when identities are free**. Shapiro and Stiglitz's worker-discipline model makes the basic continuation-value point starkly: dismissal deters shirking only because losing a job creates a real future cost; if immediate equivalent re-employment is available, dismissal loses its disciplinary force. citeturn7search7 Friedman–Resnick make the same issue identity-specific: a bad reputation matters only if resetting it entails some disadvantage. citeturn15search1

R3 actually responds to this challenge rather elegantly. A ban that can be bypassed by identity replacement does little by itself, but replacement sends the provider back into R3's high-audit newcomer state. The lasting punishment is therefore not really the ten-round name-level ban. It is the **loss of established-identity status** and the associated increase in inspection exposure. That is the correct theoretical object to model.

A second challenge concerns using a **Che-style second-score auction as though it solved quality incentives**. Che's multidimensional-auction model and the Asker–Cantillon scoring-auction literature concern price and quality as dimensions of procurement competition under specified contractual technology; they do not establish robustness when the quality number in the score is a cheap-to-inflate claim whose fulfilment is observed only by costly sampling. citeturn8search5turn8search0 More directly, Chakraborty, Khalil and Lawarree show that post-award moral hazard can make aggressive procurement competition counterproductive because winning firms need ex post rents to sustain effort; optimal procurement can limit competition or deliberately sacrifice allocative efficiency. citeturn14search3turn14search5

A third challenge concerns **adversarial evaluation**. Modern robustness methodology strongly endorses mechanism-aware adaptive attacks, but it warns that automated attack suites are not substitutes for bespoke attacks. Tramèr, Carlini, Brendel and Madry broke thirteen defences despite prior adaptive evaluations and explicitly concluded that no single automated attack methodology was sufficient across them. citeturn20search3turn20search7 RobustBench accordingly combines a standard attack suite with external adaptive evaluations rather than treating either as definitive. citeturn19search0 Your CMA-ES D1/D2 search is therefore good evidence against those strategy classes, not a certificate of incentive compatibility; the sealed H2 attacker and independently specified H1 are methodologically important rather than cosmetic.

There is also one **internal numerical check worth resolving before publication**. Under the brief's stated honest failure formula,
\[
P(\text{false failure})=\Phi(-\mathrm{tol}/\sigma),
\]
R3's \(\mathrm{tol}=0.16\) and \(\sigma=0.05\) give \(\Phi(-3.2)\approx 6.87\times10^{-4}\). At roughly 2,500 audits that is about **1.7 expected false failures**, not 34. The brief simultaneously reports 28 observed failures against 34 expected. fileciteturn0file0 This is my arithmetic, not a literature result. It suggests either that the implemented failure condition differs from the stated formula, that a different tolerance applied in that run, that substantially more than 2,500 independent failure opportunities were counted, or that “expected 34” includes another failure channel. This is exactly the kind of discrepancy a falsification-first paper should settle explicitly.

### The defensible research gap

The strongest gap is **the conjunction**, not any individual ingredient:

> A repeated procurement market with post-award hidden effort, costly noisy spot verification, a hard finite audit budget, capped monetary punishment, only finite identity-level exclusion, free or nearly free pseudonym replacement, and an admissible mechanism that may condition inspection on identity age but may not charge an ex ante entry fee or require initial collateral.

I found mature literatures for each adjacent face of this problem, but no verified paper that solves this combined mechanism-design problem. In particular, I did not find a theorem that makes **fresh-identity audit exposure itself the dues mechanism**, nor one proving that a newcomer-priority phase followed by a mixture of history-targeted and uniform inspection is optimal under free reset.

The narrower empirical claim is also defensible:

> Under an ex ante restricted sanction set that rules out the standard cheap-pseudonym fixes, does newcomer-prioritised verification materially reduce the profitability of strategically timed identity replacement relative to uniform random verification, when both use the same hard audit budget?

That framing is much safer than “we introduce targeted auditing”, “we introduce newcomer distrust”, “we introduce finite-budget inspection”, or “we introduce adversarial mechanism evaluation”. All four broader ideas already exist in substantial literatures. citeturn15search1turn13search1turn3search0turn20search3

## Annotated bibliography by concept cluster

**Costly verification, sampling and auditing.**

**Yunan Li, “Mechanism Design with Costly Verification and Limited Punishments”, *Journal of Economic Theory* 186 (2020), 105000. DOI 10.1016/j.jet.2020.105000.** The principal allocates one object among privately informed agents and can pay to verify the selected agent, but punishment for a lie is bounded. The optimal mechanism has the two-threshold structure described above, moving from unaudited pooling through probabilistic inspection to certain inspection/pooling depending on reports and market size. Relative to your market: perfect verification rather than Gaussian outcome noise; one-shot allocation rather than repeated jobs; no identity replacement; no fixed stock of audits; and the hidden variable is an exogenous type rather than endogenous post-award effort. citeturn13search2turn13search3

**Elchanan Ben-Porath, Eddie Dekel and Barton Lipman, “Optimal Allocation with Costly Verification”, *American Economic Review* 104(12) (2014), 3779–3813. DOI 10.1257/aer.104.12.3779.** Agents privately know the social value from receiving an indivisible object; transfers are unavailable, but reports can be verified at a cost. Optimal allocation can be implemented by a “favoured-agent” mechanism: a favoured participant receives the object without verification when rivals' reports stay below a threshold, while sufficiently strong rival claims are verified. This demonstrates that optimal verification is normally **selective and report-contingent**, not uniform, but it has perfect type verification, no capped continuation punishment problem, no dynamic history, and no cheap identities. citeturn0search1turn0search6

**Ian Ball and Deniz Kattwinkel, “Probabilistic Verification in Mechanism Design”, *Theoretical Economics* 20(4) (2025), 1247–1284. DOI 10.3982/TE6266.** This is especially relevant to the distinction between “an audit observes \(y\) exactly” and “\(y\) only probabilistically diagnoses effort \(q\)”. The principal chooses a test whose probability of being passed depends on the agent's type; under a screening condition the test technology admits a tractable reduced form and profit-maximising mechanisms interpolate between no verification and full verification. It is a much better conceptual match to noisy diagnostic evidence than classical deterministic verification, but still lacks an inspection stock, repeated identity state and endogenous effort/whitewashing. citeturn13search12

**Jennifer Reinganum and Louis Wilde, “Income Tax Compliance in a Principal-Agent Framework”, *Journal of Public Economics* (1985). DOI 10.1016/0047-2727(85)90035-0.** Taxpayers report privately known income and an audit reveals it; the authority chooses audit rules and penalties. Report-independent random audit rules are weakly dominated by cutoff rules, and with lump-sum taxes and fines cutoff auditing can be least-cost truth-inducing. Mapping: reported income is your claimed quality; tax evasion gain is the cost saving from under-effort; audit is output verification; penalty is refund/ban. The important mismatches are persistent taxpayers, essentially perfect discovery under audit, and penalties not crippled by a free pseudonym reset. citeturn2search1turn2search4

Mookherjee and Png provide an important qualification to “targeting beats randomness”: optimal mechanisms can intentionally use **random** auditing, but at probabilities depending on the report and insurance/incentive environment, and may reward truthful audited agents. Thus the relevant contrast is not “deterministic targeting versus randomness”; it is **uniform random coverage versus optimally differentiated random coverage**. Dilip Mookherjee and Ivan Png, “Optimal Auditing, Insurance, and Redistribution”, *Quarterly Journal of Economics* 104 (1989), DOI 10.2307/2937855. citeturn1search1turn2search18

**Limited inspections and adaptive opponents.**

**Bernhard von Stengel, “Recursive Inspection Games”, *Mathematics of Operations Research* 41(3) (2016), 935–952. DOI 10.1287/moor.2015.0762.** This is the closest finite-budget dynamic game. The inspector chooses how to spend fewer inspections than there are periods while the inspectee chooses when to violate; equilibrium strategies depend recursively on the remaining horizon and inspection stock. In the leadership version the inspector commits to a randomised inspection schedule and the inspectee acts legally while inspections remain. Your model adds multiple simultaneous jobs/providers, noisy detection, financial procurement, capacity, identity churn and a budget measured in audit cost rather than simply a number of inspections. citeturn13search1

**Blocki, Christin, Datta, Procaccia and Sinha, “Audit Games”, IJCAI 2013, pp. 41–47; stable preprint arXiv:1303.0356.** Audit games generalise Stackelberg security games by allowing the defender both to allocate audit coverage and choose a punishment level; the attacker best responds to the defender's committed mixed strategy. This is structurally close to “audit targeting plus limited sanctions”. Its optimal strategy is a **randomised targeted coverage distribution**, not a fixed recipe of half targeted and half uniform coverage; identities are persistent targets and the game is essentially static rather than a 200-round whitewashing process. citeturn3academia50turn3search10

**Blocki et al., “Audit Games with Multiple Defender Resources”, *Proceedings of AAAI* 29 (2015). DOI 10.1609/aaai.v29i1.9317.** This extension handles several heterogeneous auditing resources and gives approximation algorithms for the resulting defender optimisation. The result strengthens the case that, once targets differ in value or incentives, uniform audit probabilities are not generally optimal. It still presumes target continuity and a Stackelberg information structure in which the defender commits and the attacker best responds to coverage probabilities. citeturn3search0

**An et al., “Security Games with Limited Surveillance”, *Proceedings of AAAI* 26 (2012). DOI 10.1609/aaai.v26i1.8236.** The defender has inadequate surveillance resources and commits to randomised protection; an attacker responds strategically. This literature's “targeted plus random” structure means randomising *which strategically valuable targets receive scarce coverage*, not appending a generic uniform exploration tranche. Thus it supports R3's need for hidden randomisation, but it does not establish the 50/50 split or newcomer priority. citeturn3search1turn3search12

**Cheap identities, whitewashing and false names.**

**Eric Friedman and Paul Resnick, “The Social Cost of Cheap Pseudonyms”, *Journal of Economics & Management Strategy* 10(2) (2001), 173–199. DOI 10.1111/j.1430-9134.2001.00173.x.** Their repeated random-matching society makes identity replacement cheap and permits mistakes. Cooperation survives through a dues-paying equilibrium in which new pseudonyms receive initially poor treatment; asymptotically, no equilibrium does significantly better on cooperation under their conditions. Entry fees permit trusting newcomers but screen out low-benefit entrants; unreplaceable pseudonyms eliminate the resetting problem by creating identity persistence. Your rule forbids the easiest fee/collateral implementation and instead makes newcomers costly through inspection. citeturn15search1

**Michal Feldman, Christos Papadimitriou, John Chuang and Ion Stoica, “Free-riding and Whitewashing in Peer-to-Peer Systems”, *IEEE Journal on Selected Areas in Communications* 24(5) (2006), 1010–1019. DOI 10.1109/JSAC.2006.872882.** Users can leave and re-enter with new identities to escape reputation sanctions. A penalty imposed on *all* newcomers can deter whitewashing under broad scenarios; performance degrades especially when genuine turnover is high. This is perhaps the closest practical analogue to your newcomer treatment, but the penalty is degraded service rather than increased audit exposure, and there is no costly sample-verification budget. citeturn16search8turn16search11

**John Douceur, “The Sybil Attack”, IPTPS 2002, LNCS 2429, pp. 251–260. DOI 10.1007/3-540-45748-8_24.** Douceur shows that in a distributed system without a logically central identity authority, reliable claims that multiple identities correspond to distinct entities are generally impossible except under strong resource/co-ordination assumptions. This is broader than whitewashing: the attacker can instantiate several identities simultaneously. The relevance is that reputation and redundant verification cease to be independent defences if one economic entity can cheaply manufacture the identities on which those defences depend. citeturn15search0turn15search16

**Shabnam Seradji and Mehran Fallah, “A Bayesian Game of Whitewashing in Reputation Systems”, *Computer Journal* 60(8) (2017), 1223–1237. DOI 10.1093/comjnl/bxx018.** Their multistage incomplete-information game explicitly derives combinations of initial newcomer reputation and pseudonym cost that make co-operation preferable to whitewashing in perfect Bayesian equilibrium. That is closer than Friedman–Resnick to your desired comparative static in entry cost \(e\), although it is a reputation/service game rather than audited procurement. citeturn16search15

False-name-proof auction theory is adjacent but should not be conflated with your attack. Yokoo and coauthors study one economic agent bidding through several names, including impossibility/efficiency losses for false-name-proof combinatorial mechanisms. Your main attack is **serial** whitewashing after detection rather than simultaneous bid splitting, so this literature establishes the general fragility of anonymous mechanism design but does not answer the ban/reset problem directly. Conitzer's “Limited Verification of Identities to Induce False-Name-Proofness” is a particularly relevant bridge. citeturn16search5turn16search3

**Noisy signals and finite punishment.**

**Edward Green and Robert Porter, “Noncooperative Collusion under Imperfect Price Information”, *Econometrica* 52 (1984). DOI 10.2307/1911462.** Firms cannot perfectly infer whether bad market outcomes arise from cheating or noise, so equilibrium co-operation uses temporary punishment phases triggered by sufficiently adverse public outcomes. Innocent agents are sometimes punished, making false alarms an equilibrium cost. This is the canonical mapping for your honest provider banned after a noisy low-\(y\) audit, but it has an aggregate market signal, not costly sampled inspections, and identities cannot reset. citeturn6search16turn6search6

**Dilip Abreu, David Pearce and Ennio Stacchetti, “Toward a Theory of Discounted Repeated Games with Imperfect Monitoring”, *Econometrica* 58 (1990). DOI 10.2307/2938299.** Their self-generating-set approach characterises equilibrium continuation values under public imperfect monitoring. The key general lesson is that incentives are delivered by varying continuation payoffs after signals, often with extreme continuation values rather than mechanically proportional punishments. Your ten-round exclusion is one particularly restrictive continuation contract; free identity reset further limits the set of continuation values the operator can impose. citeturn6search1turn6search3

**Jonathan Levin, “Relational Incentive Contracts”, *American Economic Review* 93 (2003). DOI 10.1257/000282803322157115.** In repeated principal-agent relationships with noncontractible performance, continuation/termination is part of the optimal relational incentive scheme; under subjective performance evaluation termination after poor performance can arise optimally. The paper assumes a persistent bilateral relationship, which is precisely the asset destroyed by free pseudonym replacement. citeturn6search0

**Ervin Saniga, “Joint Economically Optimal Design of \(\bar X\) and R Control Charts”, *Management Science* 24(4) (1977), 420–431. DOI 10.1287/mnsc.24.4.420.** Statistical process-control design explicitly trades sampling expenditure, false alarms, corrective action and defective production when choosing control limits and sampling intensity. Mathematically this is the closest verified literature I found to jointly choosing a tolerance threshold and bearing false-positive cost. It lacks strategic manipulation and dynamic identities. citeturn7search5

I did **not** find a paper in the surveyed repeated-game/enforcement literature whose theorem literally chooses a Gaussian tolerance \(\tau\), incurs false-ban probability \(\Phi(-\tau/\sigma)\), and optimises a finite exclusion length simultaneously. That looks like a legitimate analytical subproblem rather than a result that can simply be cited away.

**Procurement with promised but under-delivered quality.**

**Yeon-Koo Che, “Design Competition through Multidimensional Auctions”, *RAND Journal of Economics* 24(4) (1993), 668–680; stable RAND/JSTOR record.** Suppliers compete over price and quality through scoring. Optimal scoring generally distorts the rewarded quality dimension relative to the buyer's raw utility, and the paper establishes the classic first-score/second-score procurement framework. It does **not** model the winning supplier announcing quality and then secretly choosing lower effort whose result is only sampled. Consequently, describing B3 as “Che-style scoring procurement” is accurate; describing Che as providing its enforcement theory would not be. citeturn8search5turn9search10

**John Asker and Estelle Cantillon, “Properties of Scoring Auctions”, *RAND Journal of Economics* 39 (2008). DOI 10.1111/j.1756-2171.2008.00004.x.** They derive equilibrium and efficiency properties of scoring auctions when suppliers have multidimensional private costs. Their result strengthens scoring auctions as a procurement benchmark but retains a contractible quality dimension, so it does not eliminate your post-award moral-hazard problem. citeturn8search0

**Indranil Chakraborty, Fahad Khalil and Jacques Lawarree, “Competitive Procurement with Ex Post Moral Hazard”, *RAND Journal of Economics* 52(1) (2021), 179–206. DOI 10.1111/1756-2171.12366.** This paper explicitly combines bidder cost heterogeneity with unobservable post-award effort. Competition can squeeze away the ex post rents needed to motivate performance, so an optimum can restrict the number of bidders or randomise allocation away from the most efficient supplier. That is a material theoretical challenge to treating allocatively efficient second-score competition and enforcement as separable modules. citeturn14search3turn14search5

**He Huang, Liming Liu, Geoffrey Parker, Yinliang Tan and Hongyan Xu, “Multi-Attribute Procurement Auctions in the Presence of Satisfaction Risk”, *Production and Operations Management* 28(5) (2019). DOI 10.1111/poms.12979.** Suppliers bid price and promised quality, subsequently exert effort, and buyer satisfaction is stochastic; the auction is paired with performance-contingent rewards or penalties. It is structurally very close to your “quality promise followed by hidden effort and noisy realised quality”, but its contracting technology permits performance-contingent monetary incentives that your admissible class sharply caps, and it does not have identity replacement. citeturn13search14

**Computation, crowdsourcing and information without ground truth.**

**Mira Belenkiy, Melissa Chase, C. Christopher Erway, John Jannotti, Alptekin Küpçü and Anna Lysyanskaya, “Incentivizing Outsourced Computation”, NetEcon 2008, pp. 85–90; stable Microsoft Research publication record.** A boss outsources tasks whose answers may be as expensive to verify as to recompute. The paper analyses random double-checking, redundant execution, rewards/fines and bounties for discovering another contractor's cheating, and also considers a malicious rather than merely rational fraction of contractors. This is one of the closest compute-specific predecessors, but its fine/credit system and persistent contractor state are much stronger enforcement instruments than your free-reset, capped-sanction environment. citeturn18search4turn18search7

**Luis Sarmenta, “Sabotage-Tolerance Mechanisms for Volunteer Computing Systems”, CCGrid 2001. DOI 10.1109/CCGRID.2001.923211.** Sarmenta compares replication/voting with “spot checking”, then combines checks with estimated worker credibility so that redundancy is directed toward uncertain workers. Voting reduces error exponentially but requires substantial duplicated computation; spot checks can be cheaper; combining credibility, checks and voting improves the reliability/cost trade-off. The close mapping is “historical credibility + selectively spent verification”; the mismatch is that credibility remains attached to the worker rather than being freely erased. citeturn18search17

**Pablo Azar and Silvio Micali, “Rational Proofs”, STOC 2012, pp. 1017–1028. DOI 10.1145/2213977.2214069.** A computationally weak verifier pays a rational prover according to a transcript so that expected payment is maximised by making the verifier learn the correct computational result. This shows that verification cost can sometimes be replaced by carefully designed informational payments, but its setting presumes objectively specified computation and much more freedom over reward structure than your operator has. citeturn18search0turn18search11

**Eli Ben-Sasson, Alessandro Chiesa, Daniel Genkin, Eran Tromer and Madars Virza, “SNARKs for C: Verifying Program Executions Succinctly and in Zero Knowledge”, IACR ePrint 2013/507.** The prover demonstrates an NP statement corresponding to correct execution of a program for up to a bounded number of steps, after compilation into a proof-friendly machine. This draws the key boundary for your paper: cryptographic verification proves satisfaction of a **formal relation**; it does not manufacture a missing semantic notion of quality. citeturn21search12

**Nolan Miller, Paul Resnick and Richard Zeckhauser, “Eliciting Informative Feedback: The Peer-Prediction Method”, *Management Science* 51(9) (2005), 1359–1373. DOI 10.1287/mnsc.1050.0379.** Instead of observing ground truth, a mechanism rewards a rater according to predictions about another correlated rater's report using proper scoring rules; truthful reporting is a Nash equilibrium under the model. It is potentially relevant when several independent workers can assess the same subjective output, but it replaces objective auditing with assumptions about correlated information and equilibrium selection rather than solving your costly-ground-truth problem directly. citeturn21search0turn21search3

Crowdsourcing provides a particularly useful adversarial analogue. Gold questions place known-answer tasks among ordinary work to estimate worker quality. Checco, Bates and Demartini show experimentally that colluding workers can learn to identify likely gold questions and behave selectively; randomisation and programmatic generation do not eliminate the attack. That is mathematically very close to an adaptive provider distinguishing “likely audited” from “unlikely audited” jobs. Alessandro Checco, Jo Bates and Gianluca Demartini, “All That Glitters Is Gold”, HCOMP 2018, DOI 10.1609/hcomp.v6i1.13332. citeturn21search1

**Evaluation against adversaries not chosen to favour the mechanism.**

**Nicholas Carlini et al., “On Evaluating Adversarial Robustness”, arXiv:1902.06705 (2019).** The paper systematises failures in empirical security evaluation and argues for threat-model clarity, attack sanity checks and strong adaptive attacks rather than trusting nominal benchmark performance. The direct translation is that “searched D2 has low gain” establishes a bound against the search procedure and strategy parameterisation, not against all economically feasible deviations. citeturn19academia30

**Florian Tramèr, Nicholas Carlini, Wieland Brendel and Aleksander Madry, “On Adaptive Attacks to Adversarial Example Defenses”, NeurIPS 2020; stable arXiv:2002.08347.** The authors break thirteen defences with mechanism-specific attacks and stress that no single adaptive attack recipe sufficed. This is perhaps the best citation for keeping H2 genuinely independent and for treating hand-designed/search-discovered attacks as complementary rather than alternatives. citeturn20search3turn20academia48

**Francesco Croce et al., “RobustBench: a Standardized Adversarial Robustness Benchmark”, arXiv:2010.09670 (2020), with continuously maintained benchmark.** RobustBench standardises evaluation with AutoAttack but explicitly invites stronger model-specific adaptive evaluations and treats the two as complementary, partly to reduce over-adaptation to a known benchmark. That maps closely to your public D1/D2 suite plus sealed H2. citeturn19search0

**American Economic Association RCT Registry, current registration policy and infrastructure.** The Registry keeps version history, permits attachments and amendments, and allows selected fields to be embargoed or documents to remain confidential until an experiment is complete. Individual registry records can expose upload timestamps and file hashes for pre-analysis-plan attachments. This gives genuine precedent for **timestamped commitments plus temporarily sealed evaluation material**, although it is normally used to freeze hypotheses/analyses before outcomes, not to freeze a mechanism's test before the mechanism itself is designed. citeturn20search0turn20search16

**Yongzhao Wang and Michael Wellman, “Regularization for Strategy Exploration in Empirical Game-Theoretic Analysis”, arXiv:2302.04928 (2023).** Iterative EGTA expands a restricted strategy set with approximate best responses; the authors emphasise that the regret quality of the best-response target materially changes strategy exploration and that straightforward best-response expansion can itself overfit. The implication for CMA-ES is that multiple restarts and fresh seeds are useful, but “no exploit found” remains conditional on the oracle and its policy space. citeturn19academia29

**Budgeted sequential inspection and terminal effects.**

**von Stengel 2016**, discussed above, is the strongest match. It explicitly makes inspection stock a state variable and solves a finite-horizon strategic game recursively. The game therefore already captures the basic “an audit unused today can be used tomorrow” feature, although it does not use a linear pacing account or terminal reserve. citeturn13search1

**Avenhaus, von Stengel and Zamir, “Inspection Games”, in *Handbook of Game Theory with Economic Applications*, Vol. 3 (2002). DOI 10.1016/S1574-0005(02)03014-X.** The inspection-game literature studies an inspectee who strategically chooses violations when the inspector has inadequate resources, often with sequential play and commitment variants. It is the right theoretical family for end-of-horizon and exhausted-budget effects. citeturn3search14

**Dynamic tax auditing**, including the model published in *Theoretical Economics* as “Optimal auditing and insurance in a dynamic model of tax compliance”, DOI 10.3982/TE737, provides another useful contrast. An optimal mechanism can condition audit probabilities on a taxpayer's history, including the duration of report patterns, so optimal monitoring is history-dependent rather than i.i.d. uniform. But the taxpayer retains a persistent identity and the authority is not allocating a fixed stock of inspections across many simultaneously active agents. citeturn2search19

I found no formal result supporting R3's exact **“reserve \(J L\) inspections so every terminal-period job is checked”** construction. Finite-horizon inspection theory instead creates state-contingent randomised coverage. That does not imply the reserve is bad in your simulator, but it means the reserve should be presented as a tested mechanism design choice rather than a known-optimal consequence of inspection-game theory.

## Assumption mapping

| Concept cluster | Closest verified work | Audit/verification resource | Penalty technology | Identity cost | Operator information and attacker adaptivity | Evaluation or key mismatch |
|---|---|---|---|---|---|---|
| Costly verification | Li 2020 | Verification of selected winner is costly; no finite intertemporal stock | Explicitly limited punishment | Identity not strategic | Reports observed; true type perfectly revealed if inspected | Static Bayesian optimisation, no simulated attacker. citeturn13search2 |
| Strategic inspection | von Stengel 2016 | Exactly \(m\) inspections over \(n>m\) periods; unused inspections remain | Detection loss specified in game payoffs | Persistent inspectee | Inspectee strategically times violations; commitment version studied | Analytical equilibrium; no noisy signal or market entry. citeturn13search1 |
| Cheap identities | Friedman–Resnick 2001 | No scarce auditing technology | Reputation/service treatment creates continuation incentives | Pseudonym replacement cheap | Histories are pseudonym-specific; players know reputation state | Analytical repeated matching; newcomer “dues” but not audits. citeturn15search1 |
| Noisy trigger punishment | Green–Porter 1984 / Levin 2003 | Signal arrives exogenously rather than being purchased | Temporary punishment/termination through continuation play | Relationship persistent | Noisy performance signal; deviations strategic | Equilibrium repeated-game analysis, no whitewashing. citeturn6search16turn6search0 |
| Procurement moral hazard | Chakraborty–Khalil–Lawarree 2021 | No scarce sampling budget | Incentive contract preserves ex post rent | Firms persistent | Cost and effort private; buyer designs procurement + incentive scheme | Shows competition and performance incentives cannot generally be separated. citeturn14search3 |
| Outsourced compute | Belenkiy et al. 2008 | Random double-checking or redundant execution consumes compute | Rewards, fines and bounties | Contractor accounts effectively persistent | Rational or malicious contractors; boss selects checking scheme | Stronger monetary/identity assumptions than yours. citeturn18search4 |
| Adversarial evaluation | Tramèr et al. 2020 / RobustBench | Evaluation effort is itself a scarce search resource | Not an enforcement model | Not applicable | Attacker knows defence and adapts specifically to it | Strong warning against interpreting one automated search family as worst case. citeturn20search3turn19search0 |
| Sequential reserve | von Stengel 2016 | Remaining horizon and remaining inspections jointly determine coverage | Inspection penalty | Persistent inspectee | Adaptive strategic timing over finite horizon | No theorem for fixed linear pacing + deterministic terminal full coverage. citeturn13search1 |

Two cross-cutting differences dominate this table. **First, nearly every formal deterrence model makes punishment attach to a persistent economic agent.** Your operator cannot do that. **Second, most verification models assume either a perfectly revealing inspection or a formal correctness relation.** Your audit observes a noisy output realisation even when the promise concerns expected quality. Ball and Kattwinkel's probabilistic verification is therefore a useful recent bridge between these literatures. citeturn13search12

There is also a significant distinction between **committed and adaptive adversaries**. Stackelberg security/audit games normally let the defender commit to a mixed strategy and the attacker best respond to its distribution; your provider can additionally condition later decisions on realised audit outcomes, remaining time and the identity state created by earlier enforcement. citeturn3search0turn13search1

## Theorems, lower bounds and impossibility results most relevant to the mechanism

### Limited-punishment costly verification

Li's 2020 result is the cleanest theorem to cite when arguing that capped punishment changes audit allocation qualitatively. Under his one-object, private-value environment with costly perfect verification and a bounded punishment, an optimal mechanism is governed by lower and upper thresholds \(v^\ell\leq v^u\). Below \(v^\ell\), reports are pooled and no inspection occurs; in the intermediate region the highest report wins and is inspected with positive probability; beyond \(v^u\), high reports are pooled and the selected agent is inspected with probability one. For a sufficiently large number of agents the thresholds coincide, giving a shortlisting implementation. citeturn13search2turn13search3

**Implication for your claims:** targeted verification under limited sanctions is known. What is not known from Li is how to choose the target using pseudonym age, how to allocate a hard repeated audit stock, or how to deter effort shading when the inspection itself is a noisy draw from performance.

### Targeting can strictly beat report-independent random auditing

Reinganum and Wilde's 1985 tax model establishes, under its income-reporting and enforcement assumptions, that random auditing independent of reports is weakly dominated by cutoff auditing; with lump-sum taxes and fines, cutoff rules are least-cost mechanisms for inducing truthful reporting. citeturn2search1turn2search4

This should prevent an overbroad “uniform random auditing is the natural optimum” claim. Uniform random inspection becomes a compelling benchmark primarily when all currently eligible jobs are exchangeable from the operator's information set. Once there is payoff-relevant public state such as report, age, previous audit exposure, target value or predicted attack likelihood, the audit and security-game literatures generally exploit it. citeturn3search0turn3search1

**Own derivation for the symmetric case.** If all jobs have exactly the same cheating gain, detection technology and sanction, and the adversary can freely choose any job after seeing all public differentiation, symmetry makes equal marginal coverage the natural minimax solution. This conclusion does not survive heterogeneous incentive states. R3 deliberately creates such heterogeneity through identity age.

### Cheap pseudonyms impose a newcomer cost

Friedman and Resnick's substantive impossibility result is not “cooperation is impossible with free identities”. It is more precise and more useful: under their large repeated random-matching environment with finite lives, cheap identity changes and a small non-vanishing chance of mistakes, no equilibrium can sustain significantly more cooperation than their dues-paying construction. Efficient co-operation therefore comes with a social cost somewhere: mistreat newcomers, charge entry, or make pseudonyms non-replaceable. citeturn15search1

Feldman et al. reinforce this in a dynamic whitewashing model: a newcomer penalty is an effective anti-whitewashing instrument, with the obvious welfare cost that legitimate newcomers suffer too and the system degrades when turnover is large. citeturn16search0turn16search11

Your admissible mechanism class therefore rules out two of the cleanest literature solutions:

* it cannot make identity reset directly expensive through an **entry fee or upfront bond**;
* it cannot use **unreplaceable or externally certified identity** as the reputation anchor.

It may still impose initial distrust through allocation or inspection state, and it may withhold a small bond only after receipts exist. That restriction is economically consequential rather than innocuous.

### A direct audit-rate lower bound for your sanction cap

I did not find a published theorem with exactly your state variables \(p,g,e,L\), refund cap and reset rule. There is, however, a simple incentive constraint, closely related to Becker's expected-sanction calculus and to the worker-discipline logic of Shapiro–Stiglitz. Becker's general enforcement model makes behaviour depend on apprehension probability and punishment severity; Shapiro–Stiglitz makes dismissal effective only through the continuation loss it causes. citeturn14search0turn7search7

Let

\[
g
\]

be the incremental gain from cheating on a job relative to truthful effort,

\[
p
\]

the probability that the relevant deviation is audited,

\[
d
\]

the conditional probability an audit generates a sanction given the deviation,

\[
M
\]

the monetary loss when sanctioned, including refund/forfeiture, and

\[
\Delta V
\]

the continuation-value loss from enforcement and/or resetting to a new identity, including an entry cost \(e\).

Then the one-deviation incentive condition is

\[
p\,d\,(M+\Delta V)\ge g,
\]

hence

\[
\boxed{p\ge \frac{g}{d(M+\Delta V)}} .
\]

This displayed inequality is **my reduction of your model, not a quoted theorem**.

It gives several useful cases.

If identity reset is free and a fresh identity receives *exactly the same continuation opportunity* as the burned identity, then a name-level ban has no continuation value:

\[
e=0,\qquad V_{\rm fresh}=V_{\rm established}
\quad\Longrightarrow\quad
\Delta V_{\rm ban}=0.
\]

Deterrence then requires

\[
p\ge \frac{g}{dM}.
\]

So **free identity does not by itself produce an impossibility** when an audited job can lose enough money. If \(dM\ge g\), sufficiently high auditing can still deter. The true impossibility is

\[
d(M+\Delta V)<g
\]

even at \(p=1\). In that case no audit fraction at or below one can deter that deviation under the admissible sanction cap.

If \(M=0\), \(e=0\), and a fresh identity is completely equivalent to an established one, then any positive cheating gain is undeterrable by a bypassable finite ban alone. This is the whitewashing analogue of Shapiro–Stiglitz's observation that firing ceases to discipline a worker when equivalent immediate re-employment carries no loss. citeturn7search7

R3 changes the calculation because

\[
V_{\rm fresh}<V_{\rm established}
\]

when new identities face intensive auditing. Thus

\[
\Delta V_{\rm reset}
=
V_{\rm established}-V_{\rm fresh}+e>0
\]

can hold even at \(e=0\). In economic terms, **identity age becomes an endogenous relationship-specific asset**. This is the strongest theoretical interpretation of your newcomer-priority phase.

### Finite inspection stocks need state-dependent strategies

von Stengel proves existence and gives an explicit recursive solution for a sequential game with a limited number of inspections across more periods than can be inspected. Under his regularity assumptions the inspector's equilibrium behaviour can be expressed as a function of remaining periods and inspections, and in the leadership version commitment to the randomised inspection schedule can induce legal behaviour while inspection capacity remains. citeturn13search1

Two implications matter for R3.

First, **carry-over itself is entirely standard**: an unused inspection remains part of tomorrow's state.

Second, a predictable temporal hole is strategically dangerous. A finite-horizon audit rule should be evaluated against an adversary that knows the entire pacing rule and optimises the *timing* of cheating. The inspection-game literature supports randomising temporal exposure rather than merely preventing audit exhaustion. It does not establish that reserving enough capacity to audit every last-\(L\)-round job is optimal. citeturn13search1turn3search14

### What “targeted plus random” really means

Security and audit games do establish a strong precedent for **targeted randomisation**: the defender optimises unequal marginal coverage across targets, then randomises over feasible audit allocations so that the attacker cannot condition on the realised allocation. citeturn3search0turn3search1

That is not the same mathematical claim as

\[
50\% \text{ targeted}+50\% \text{ uniform}.
\]

I found no theorem making that split optimal or universally near-optimal. A fixed uniform tranche is better interpreted as an **exploration/robustness hedge against model misspecification**: it guarantees nonzero exposure to attacks not captured by the targeting statistic. That interpretation fits adversarial robustness methodology better than classic Stackelberg optimisation. citeturn19search0turn20search3

## Claims to avoid and claims that remain defensible

### Claims that would overstate novelty

**“We show that costly verification should be targeted rather than uniform.”** Too broad. Costly-verification, tax-audit and security-game models already generate report- or target-dependent auditing. citeturn13search2turn2search1turn3search0

**“We introduce random auditing as a deterrence mechanism for outsourced computation.”** Already present directly in Belenkiy et al., and spot-checking/redundancy have a long volunteer-computing history. citeturn18search4turn18search17

**“We show cheap identities require initial distrust.”** Friedman–Resnick and Feldman et al. contain this idea squarely. citeturn15search1turn16search0

**“We show a limited inspection stock creates a dynamic allocation problem.”** Inspection games already solve precisely that kind of finite-resource timing game. citeturn13search1

**“A mixture of targeted and random audits is novel.”** Randomised targeted coverage is standard in security games and random auditing conditioned on information appears in economic audit mechanisms. citeturn3search0turn1search1

**“Second-score procurement handles strategic quality reporting.”** Classic scoring-auction results do not establish truthful *delivery* of unverifiable quality, and later procurement work shows post-award moral hazard can fundamentally alter the optimal auction. citeturn8search0turn14search3

**“Automated search demonstrates robustness to adaptive adversaries.”** It demonstrates robustness to the searched policy class and optimiser. Modern adversarial-evaluation work is specifically sceptical of making the stronger extrapolation. citeturn19academia30turn20search3

### Claims that look genuinely defensible

**A verification-based version of “pay your dues”.** The cheap-pseudonym literature makes newcomers bear worse service, an entry cost, or loss of reputation; I found no formal result in which the scarce resource deliberately spent on fresh pseudonyms is *verification itself*. Framing R3 as “audit dues” cleanly distinguishes it from the underlying newcomer-disadvantage idea. citeturn15search1turn16search0

**The interaction of a hard verification budget, capped punishment and whitewashing.** The papers closest on each dimension omit at least one of the other two: Li has costly verification and limited punishment but no reset; von Stengel has scarce sequential inspection but no reset/market; Friedman–Resnick has reset but no scarce verification technology. citeturn13search2turn13search1turn15search1

**An empirical comparison holding the admissible sanction set fixed.** Much of the literature “solves” pseudonym churn using instruments your registered class deliberately forbids, especially entry fees, collateral/stake or persistent identity. Comparing audit policies after eliminating those instruments asks a meaningfully different question.

**Identity age as a mechanism state that converts an otherwise bypassable ban into a real continuation-value loss.** The ingredients are old, but the mechanism link is unusual: ban → reset → newcomer state → elevated verification probability → reduced value of reset.

**A preregistered, falsification-oriented mechanism search with genuinely sealed adversaries.** Preregistration, version history, embargoes and adaptive red teaming separately have strong precedents, but I found no exact mechanism-design precedent combining “freeze tests and success criteria before designing the mechanism”, a third-party sealed strategic family, optimisation-discovered attacks, and fresh final simulation seeds. A claim should be phrased as “we are unaware of a prior mechanism-evaluation protocol combining these features”, not “this is the first”. citeturn20search0turn20search16turn20search3

**A negative result about bans under free reset, if proved formally inside your admissible class.** The intuition exists in efficiency wages and cheap-pseudonym work, but a theorem specialised to noisy job audits, bounded refunds/bonds, finite bans and immediate zero-cost re-entry would still be useful. citeturn7search7turn15search1

### Assumptions that deserve explicit defence

The literature will ask why an identity-age-dependent audit rule is permissible while stronger identity remedies are not. The answer should be institutional, not merely computational: the operator can observe *when an opaque token first appeared* without learning whether two tokens are the same real entity. Thus age is observable and relabelling-invariant in the relevant sense, even though persistent real-world identity is unavailable.

The literature will also ask whether the proposed claims concern **equilibrium implementation or empirical attack resistance**. The simulator searches unilateral deviations against honest-max opponents. That is a strong empirical stress test, but it is not a Bayes-Nash or perfect-public-equilibrium characterisation of the full ten-provider game. The paper should say so plainly.

Finally, cryptographic verifiability should not be dismissed simply because output is stochastic. SNARK-style systems verify a formal computation relation, and randomness can itself be committed as part of the witness/input. The real boundary is whether the buyer's desired notion of quality can be expressed as a formal, efficiently checkable relation over committed information. citeturn21search12

## What deployed systems actually do

The most striking practical finding is that the systems I could verify generally **do not accept your admissible class**. They buy security by requiring stake, durable reputation, redundant execution, trusted hardware, provider certification, or user inspection. That makes your no-upfront-bond/free-re-entry restriction genuinely severe.

### Golem

Current Golem documentation describes a provider reputation layer based on information including task success, provider age, uptime and performance, and requester-side filters can explicitly require a minimum provider age or success rate. Reputation-related probe/tasks gather information independently of an arbitrary requester's semantic judgement of its own workload. citeturn10search9turn10search0

The close mapping is significant: **provider age is already treated as information about trustworthiness**. A provider resetting its identity gives up its accumulated age/reputation. That creates initial distrust without necessarily levying a literal fee.

I found no Golem documentation specifying a universal fraction \(x\%\) of arbitrary marketplace jobs that the platform independently re-executes or semantically audits. Thus there is no justified number to compare with your approximately 25% sampled audit coverage. The mechanism is reputation/filtering plus requester-defined application logic rather than a common statistical inspection budget. citeturn10search9turn10search0

### iExec

iExec's Proof-of-Contribution material is substantially stronger than your admissible model. Workers have reputation, are required to lock stake, are assigned in ways intended to reduce collusion, and results can be replicated until a requested confidence/consensus condition is met. Erroneous participation can lose stake. citeturn11search11turn11search0

Consequently there is **no fixed verification fraction analogous to \(\beta\)**. Redundancy is task/confidence dependent: additional workers may execute the same task until consensus is sufficient. Documentation also ties worker reputation to wallet identity and allows pools/schedulers to impose reputation or stake requirements, which makes abandoning a bad identity economically much less free than in your baseline. citeturn11search0turn11search3

Older PoCo descriptions also expose an important applicability condition: redundancy-based consensus is most straightforward when executions are deterministic enough for workers' outputs to be compared. Non-deterministic jobs require different handling. citeturn11search3

So iExec is not evidence that R3 is unnecessary. It is evidence that deployed systems commonly solve the same problem using instruments R3's admissible class intentionally removes.

### Akash

Akash's provider-auditing documentation concerns **provider attributes and infrastructure**, including validation of claimed properties and benchmark-style workloads, rather than sampling arbitrary tenant computations and declaring their semantic outputs correct. Tenants may select providers based on signed/audited attributes. citeturn10search1turn10search2

Accordingly, I found no platform-level percentage of tenant jobs whose result is independently recomputed or audited for semantic correctness. In your vocabulary, Akash audits the *supplier capability claim* much more than the *delivered quality of each purchased job*.

Current Akash design material also recognises that manually advertised provider attributes depend on trust and can be falsely stated, motivating more automated verification. citeturn10search11 That is a close analogue to your distinction between a claimed \(c\) and what a provider actually supplies.

### Render Network

Render exposes rendered frames to creators as watermarked previews and lets the creator approve or reject frames individually or in batches. If the creator takes no action within the documented time window, frames can be automatically approved; rejected frames are sent to another node for re-rendering, subject to retry limits. citeturn10search7turn10search13

This means the **available review surface can cover every frame**, but the fraction actually inspected by a human is user-selected and is not a fixed protocol audit rate. It therefore resembles buyer-side acceptance inspection more than your operator-funded random sample.

Node reliability affects reputation/status and repeated failure can lead to quarantine or other node consequences; participation also involves a managed node/application relationship rather than costlessly interchangeable opaque provider tokens. citeturn10search3

### Bittensor

Bittensor does not attempt universal objective output verification. Validators query miners and assign scores according to each subnet's task-specific utility function; Yuma Consensus aggregates validator judgements in a stake-weighted mechanism intended to resist strategically distorted scoring under its trust assumptions. citeturn12search8turn12search10

There is no single network-wide answer to “what percentage of outputs are verified”, because query/scoring frequency and the definition of utility are subnet-specific. The key identity assumption is also stronger than yours: registration, hotkeys/UIDs, validator permits and stake/economic weight create identity/resource persistence rather than zero-cost reset. citeturn12search9

This is conceptually closer to **peer evaluation** than ground-truth auditing. That places it nearer to peer-prediction and reputation mechanisms than to your operator purchasing an exact \(y\) measurement. citeturn21search0

### Crowdsourcing

Crowdsourcing provides perhaps the closest operational analogue to your audit problem. Requesters can insert known-answer “gold” items among ordinary jobs and use them to estimate worker reliability. With a small supply of gold labels, periodic insertion can outperform using the same small set only as initial training; one HCOMP study found that pattern with fewer than 25 available gold labels in its data. citeturn21search7

But gold tasks are strategically learnable. Checco, Bates and Demartini demonstrate an attack in which colluding workers infer which questions are likely to be gold and selectively behave well on those questions, even under several forms of randomisation. citeturn21search1 This is an unusually close empirical precedent for why your evaluation must include providers that adapt behaviour to **audit likelihood rather than only past punishment**.

### What cryptographic verification does and does not remove

The phrase “probabilistic jobs cannot be cryptographically verified” is too strong.

SNARK-style verifiable computation can establish that a specified program was executed consistently with committed inputs and witnesses. A randomised computation can be converted into such a statement by committing the randomness or a seed. citeturn21search12 What it cannot do by itself is decide whether the formal computation being proved corresponds to the buyer's latent notion of *good service*.

The jobs that still require empirical audit, trusted external measurement or human judgement therefore include:

**Subjective or perceptual quality.** “This image is aesthetically good”, “this answer is helpful”, or “this annotation captures the intended meaning” has no unique formal correctness relation unless an evaluator/model is itself specified.

**External-world claims.** A proof can demonstrate what software did to supplied bytes; it cannot establish that a sensor reading faithfully reflects the physical world without some trusted measurement/attestation layer.

**Generalisation or future performance.** One can prove that a model-training algorithm executed exactly and even prove a metric on a committed test set. That does not prove that the trained model will attain an unspecified quality level on future, hidden or distribution-shifted data.

**Approximate quality whose benchmark remains hidden from the worker.** If the operator deliberately keeps its evaluation distribution or human rubric secret because revealing it would invite overfitting, turning the whole criterion into a public proof relation may defeat the purpose.

**Open-ended computation where “effort” rather than execution correctness is the promised object.** A cryptographic proof can verify a prescribed sequence of training operations; it does not prove that this sequence was economically the “right amount of effort” or that a buyer's subjective benefit meets the claim.

Thus cryptographic proof removes your audit problem only for the subset of jobs where “quality” can be replaced by **formal execution correctness over committed information**. The distinction is specification, not deterministic versus stochastic computation. citeturn21search12

## Open questions, unresolved searches and recommendations for positioning

### Questions the literature does not appear to settle

**No exact newcomer-first auditing theorem.** Searches across costly verification, whitewashing, Sybil defence, audit games and dynamic tax compliance found newcomer penalties, age/reputation discounts and optimally targeted inspection, but not a model proving “inspect jobs from the newest identities first” under a shared inspection budget. The closest conceptual pieces are Friedman–Resnick's dues and Feldman et al.'s newcomer penalty. citeturn15search1turn16search0

**No exact free-entry/capped-ban audit lower bound matching your environment.** Whitewashing papers derive conditions on entry cost/reputation, and standard deterrence theory combines detection probability and sanction severity, but I found no theorem for your exact refund-plus-finite-ban-plus-small-receipts-bond admissible set with immediate re-entry and noisy job-level auditing. Seradji–Fallah is the closest explicit entry-cost comparative-static model. citeturn16search15

**No exact Gaussian-tolerance/finite-ban optimum.** Repeated games analyse noisy trigger punishments and statistical process control prices false alarms, but I did not find a result simultaneously choosing a Gaussian acceptance tolerance, audit probability and finite exclusion duration against strategic effort. citeturn6search16turn7search5

**No verified theorem for the R3 50/50 residual split.** Audit/security games justify randomised nonuniform coverage, but not a fixed half targeted/half uniform decomposition. citeturn3search0turn3search1

**No verified theorem for the terminal full-audit reserve.** Recursive inspection games are the natural formal benchmark and provide state-dependent temporal mixing, but the surveyed literature did not produce a result selecting an “audit every job during the last \(L\) rounds” reserve. citeturn13search1

**No exact prior evaluation protocol matching yours.** I found strong precedents for prospective registration, version history, embargoed/confidential plans and timestamped file commitments in economics, and separately for defence-aware independent attacks in computer security. I did not find an exact precedent in mechanism design for freezing the success criteria and attack suite before the mechanism is designed while retaining a third-party sealed strategic attacker for final evaluation. citeturn20search0turn20search16turn20search3

### Searches that did not yield a sufficiently close verified result

The unsuccessful or only partially successful searches included variants of **“newcomer-first auditing cheap pseudonyms / whitewashing”**, **“finite ban free re-entry audit rate”**, **“hard audit budget carry-over reserve inspection”**, **“terminal reserve finite-horizon inspection game”**, **“Gaussian noisy signal threshold temporary exclusion optimal tolerance”**, and **“preregister mechanism before design sealed attacker”**. They returned adjacent models rather than the joint structure above.

I also did not obtain a sufficiently authoritative, current primary source in this pass to make quantitative claims about **Truebit's current deployed verification rates**, so I would not put a number for Truebit in the paper without a separate source check. The older outsourced-computation papers, current iExec documentation and formal verifiable-computation literature are sufficient to establish the conceptual comparison without inventing one. citeturn18search4turn11search0turn21search12

### The strongest falsification tests suggested by prior work

The literature points to attacks more demanding than the current D2 family.

One is an **audit-hazard attacker** that estimates the conditional audit probability from public state and cheats only where the expected sanction falls below its effort saving. This is the direct best response suggested by audit/security games. citeturn3search0turn3search1

A second is a **gold-question detector** analogue: use age, job position, round, prior quota consumption, the number of other newcomers and remaining horizon to infer whether a job is likely to be in R3's priority, targeted or random tranche, then vary effort *within the provider's six jobs* accordingly. The crowdsourcing attack literature shows why merely randomising individual keys need not make audit likelihood unlearnable when the mechanism has observable structure. citeturn21search1

A third is a **finite-horizon timing attacker** that optimises cheating jointly over remaining audit stock and remaining rounds rather than reacting only to its own most recent failure. Recursive inspection theory makes the remaining-resource state the central state variable, so this is a more theoretically grounded adversary than a simple markup-decay process. citeturn13search1

A fourth is a **reset-option attacker** that solves explicitly for whether to retain an established identity or exercise the reset option. Its decision should depend on the difference \(V_{\rm established}-V_{\rm fresh}\), not simply “reset after every failed audit”. That directly tests whether newcomer-first inspection creates enough endogenous identity capital to deter whitewashing.

A fifth is an **independently engineered attacker rather than another optimiser over the designers' vocabulary**. Tramèr et al.'s security lesson is that a defence's author often fails to imagine the transformation that removes the protection; adaptive red teaming therefore needs diversity in attacker construction, not merely a larger optimisation budget over one family. citeturn20search3 This makes the sealed H2 component of the protocol particularly valuable.

### Recommended contribution statement

The literature supports a contribution claim along these lines:

> Existing costly-verification mechanisms optimise report-contingent inspection under persistent identities; inspection games optimise scarce inspections against strategic timing; and cheap-pseudonym models sustain co-operation by making newcomers pay dues. We study the intersection in a repeated compute-procurement market where verification is costly and noisy, monetary punishments are capped, exclusion is finite, and a punished provider can immediately re-enter under a fresh pseudonym. Because ex ante fees, identity certification and initial collateral are excluded, we test whether allocating scarce verification disproportionately to new identities can make identity replacement itself costly in continuation value. We compare this rule with uniform auditing under search-optimised and independently sealed adaptive deviations using a prospectively registered falsification protocol.

Every major ingredient in that statement has prior art, but **their interaction is the gap**. citeturn13search2turn13search1turn15search1turn20search3

The most important conceptual result to seek analytically is then not “targeting beats randomness”. It is a condition of the form

\[
p_{\rm new}dM
+
\bigl(V_{\rm established}-V_{\rm new}\bigr)
+e
\;\ge\;
\text{value of cheating/resetting},
\]

together with the welfare cost imposed on genuinely honest entrants. Friedman–Resnick tells you that such a newcomer cost should exist somewhere; your mechanism asks whether **scarce verification rather than fees, collateral or deliberately poor service can supply it efficiently**. citeturn15search1

That is the part of the project for which the surveyed literature provides the clearest motivation but, on the verified sources found here, not the answer.