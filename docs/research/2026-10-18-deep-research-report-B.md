# Deep research report B (second run, pasted 2026-10-18; verbatim; citations unverified by us, several differ from report A)

Note by the authors: this run was pasted without its citation links. Report A (`2026-10-18-deep-research-report-A.md`) marks its own derivations and verified its references; where the two disagree (for example report B's "Friedman and Resnick Proposition 2, alpha/(2-alpha)" bound, its Dresher 1962 attribution of terminal reserves, and its deployed-system percentages), report A's more careful statements take precedence until a primary source is checked. Both reports agree on the closest models (costly verification with limited penalties, cheap pseudonyms, inspection and audit games), on the deterrence arithmetic under capped penalties and free re-entry, on the positioning of newcomer-first auditing as an audit-based form of "paying your dues", and on the pre-registered falsification protocol as the methodological contribution.

## Executive summary (report B)

The three closest models: Mylovanov and Zapechelnyuk (2017) on optimal allocation with ex post verification and limited penalties; Friedman and Resnick (2001) on the social cost of cheap pseudonyms; Blocki, Christin, Datta, Procaccia and Sinha (2013) on audit games against adaptive attackers.

Key results it says must be cited: the Becker (1968) and Shapiro-Stiglitz (1984) deterrence condition under limited liability (with penalties capped at the escrowed payment and free re-entry, deterrence is impossible when the cheating gain exceeds the payment, and otherwise needs audit probability at least gain over payment); an inefficiency lower bound for free identities it attributes to Friedman and Resnick; sequential inspection pacing with terminal reserves it attributes to Dresher (1962) and Avenhaus, von Stengel and Zamir (2002).

Challenged assumptions: banning pre-receipt bonds forces all deterrence onto the audit budget; auditing newcomers first spends scarce audit capital on agents who can defect and re-enter.

Claimed gaps: audit-intensive dues-paying under bounded penalties; falsification-first pre-registration against search-optimised attackers.

## Annotated bibliography (report B, abbreviated to the entries and the stated differences)

Cluster 1 (costly audits of a sample): Townsend 1979 (JET); Border and Sobel 1987 (REStud); Mookherjee and Png 1989 (QJE); Ben-Porath, Dekel and Lipman 2014 (AER, favoured-agent mechanism); Mylovanov and Zapechelnyuk 2017 (AER, limited penalties: bunching at top and bottom, shortlisting with many agents).

Cluster 2 (limited inspections, adaptive opponent): Avenhaus, von Stengel and Zamir 2002 (Handbook of Game Theory); Blocki et al. 2013 (IJCAI audit games, NP-hardness, FPTAS, saturate high-priority targets and randomise the rest); Yin, An and Tambe 2012 (AAMAS, mixed Stackelberg strategies).

Cluster 3 (cheap identities): Friedman and Resnick 2001 (JEMS); Feldman, Papadimitriou, Chuang and Stoica 2006 (IEEE JSAC, whitewashing invades reciprocity when identity cost is zero); Yokoo, Sakurai and Matsubara 2004 (GEB, false-name bids).

Cluster 4 (noisy trigger punishment): Green and Porter 1984 (Econometrica); Abreu, Pearce and Stacchetti 1986 (JET) and 1990 (Econometrica); Levin 2003 (AER); Duncan 1956 (JASA, economic design of X-bar charts: the tolerance threshold against Phi(-k)).

Cluster 5 (procurement with under-delivery): Che 1993 (RAND); Asker and Cantillon 2008 and 2010 (RAND); Laffont and Tirole 1993 (MIT Press).

Cluster 6 (compute and data platforms): Belenkiy et al. 2008 (NetEcon: deterrence iff fine over reward at least (1-p)/p); Azar and Micali 2012 (STOC rational proofs); Dasgupta and Ghosh 2013 (EC, peer prediction with endogenous effort).

Cluster 7 (evaluation against undesigned adversaries): Wellman, Tuyls and Greenwald 2013 (JAIR, EGTA); Conitzer and Sandholm 2002 (UAI, automated mechanism design).

Cluster 8 (budgeted sequential inspection): Dresher 1962 (RAND memorandum); Avenhaus and Canty 2005 (EJOR).

## Report B's derivations (its own, not quoted theorems)

Deterrence under bounded penalties and free entry: with penalty capped at the current payment P and no continuation loss from a ban under free re-entry, cheating pays whenever p P < Delta; the minimum audit probability is Delta / P; if Delta > P no audit probability deters. Report B applies this to our parameters to explain why random audits at a quarter coverage fail against identity hopping.

Gaussian tolerance: false-alarm rate Phi(-tol/sigma); detection rate Phi((Delta - tol)/sigma); an optimal-tolerance programme balancing false bans against deterrence.

Dynamic inspection pacing: a recursive value V(t, m) with a terminal all-audit phase; report B presents the terminal reserve as consistent with Dresher-type games (report A disagrees: no theorem selects a deterministic terminal full-coverage reserve).

## Deployed systems (report B's table, unverified figures)

Bittensor (stake-weighted validator scoring, Yuma consensus, registration fee burn or lock, deregistration); Truebit (verification game, forced errors, large bonds, slashing; sub-1 percent on-chain audits claimed); iExec (proof of contribution, replication k at least 3, staked RLC, slashing); Render (tile spot checks 1 to 5 percent claimed, tiered reputation); Akash (infrastructure SLA only, no computational audit); crowdsourcing (5 to 10 percent gold tasks claimed, KYC identities). Report B's percentages were not sourced; report A found no platform-level verification fractions for Golem, iExec, Akash, Render or Bittensor and declined to put numbers on Truebit.

## Claims to avoid (report B)

Vulnerability of random auditing to cheap pseudonyms (Friedman and Resnick; Feldman et al.); second-score auctions do not solve post-award moral hazard (Che; Asker and Cantillon; Laffont and Tirole); mixed strategies dominate deterministic inspection (inspection and security games); trigger-style temporary punishments under noise (Green and Porter; Abreu, Pearce and Stacchetti); fines capped at the current payment cannot deter without repeated-game surplus (Becker; Belenkiy et al.).

## Gaps (report B)

Audit-intensive dues under banned pre-receipt collateral; dynamic budget allocation with carry-over and a terminal reserve inside a two-sided market with endogenous quality claims; pre-registered falsification against heuristic-search adversaries with a sealed attack suite.

## Open questions (report B)

The exact deterrence threshold for newcomer-first audit quotas as a function of the budget fraction, entrant capacity and ban length; the joint optimum of tolerance and ban length against strategic shading; an optimal mechanism for scoring auctions with a hard audit budget and free re-entry.
