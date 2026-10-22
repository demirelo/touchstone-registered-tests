# Review prompt for GPT Pro (paste this; attach the files listed under "Materials")

You are a senior referee and area chair with expertise in mechanism design (costly verification, repeated games, procurement), algorithmic game theory and multi-agent systems, security economics (Sybil and whitewashing, audit games), and empirical methodology (pre-registration, adversarial evaluation). Review the attached paper as you would for a top venue, then go beyond a normal review on four tasks: novelty, claims, venue fit, and bibliography. Be adversarial and specific. Do not soften findings.

## Materials (attached)

1. `main.pdf` — the paper.
2. `reset-deterrence.md` — the theory document with full proofs and its checks (`checks-2026-10-21.md`).
3. `final-evaluation-README.md` — the registered verdict, per-cell tables, and run history.
4. `robustness-results.md` — the 292-cell exploratory robustness results with predictions beside outcomes.
5. `amendments/` — the four amendment notes, with the reasons and timing of each change.
6. `citations.md` — our verification log for every reference.

## Task 1: Novelty

Determine whether the paper's contribution already exists, in any field and under any vocabulary. Search by concept, not by our words. The mechanism is: under free identity replacement and no fees or collateral before receipts, a market spends its scarce verification budget preferentially on new identities ("audit dues"), so that replacing an identity buys a period of heavy inspection instead of a clean slate. Look for equivalent ideas in at least these areas:

- costly state verification, costly verification mechanisms, ex post verification with limited penalties;
- cheap pseudonyms, whitewashing, Sybil resistance, newcomer treatment, "paying your dues", reputation with entry;
- inspection games, audit games, security games, randomised and targeted inspection, finite inspection stocks;
- spot-checking, credibility-based fault tolerance and sabotage tolerance in volunteer and grid computing (we cite Sarmenta 2002; find anything closer);
- crowdsourcing quality control (gold questions for new workers, qualification periods), probation periods in labour economics, tax and customs audit selection of new firms or importers, new-seller verification on marketplaces;
- decentralised compute and data markets (Golem, iExec, Akash, Render, Bittensor, Truebit, verifiable computation and its economic layer);
- mechanisms with verification for scheduling and load balancing.

For each close work: citation (venue, year, DOI or stable URL), what it does, how it maps onto our model (what plays the role of the audit, the sanction, the identity, the budget), and whether it anticipates our rule, our analysis, or our evaluation protocol. Then state plainly which of our contributions are new, which are incremental, and which are already known. Mark anything from your own reasoning rather than a source.

## Task 2: Claims

For every claim in the abstract, the introduction, and the results, check it against the attached evidence and the stated assumptions. In particular:

- the registered verdict (original FAIL, amended PASS) and its qualifiers: amended after development results; interval admission with B3 as a proxy;
- the attribution claim that R3 and B3 differ only in audit selection and pacing;
- the theory: are the lemma, corollary, theorem, and proposition correct as stated, are the assumptions complete, does the paper overstate their scope (stationary same-offer plans only; not the adaptive family, not coalitions)?
- the robustness claims: reused development seeds, parameter transfer, incomplete searches, failed twin controls, and the three failure modes (reserve collapse, high-noise efficiency loss, coalition overload);
- the protocol: does the chronology support "prospectively registered", given four amendments? What would a skeptical referee say about forking paths, and is our disclosure adequate?

List each overclaim or unsupported statement with the exact sentence and a corrected wording.

## Task 3: Venue fit

Recommend venues and rank them, with reasons and with each venue's next submission deadline after October 2026 (verify the dates). Consider at least: ACM EC 2027, AAMAS 2028, NeurIPS 2027 (main and Datasets and Benchmarks), ICML 2027, AAAI 2027 or 2028, IJCAI 2027, WINE 2026 or 2027, SAGT, GameSec, Financial Cryptography, Management Science or Operations Research (journal), and relevant workshops. For the top two venues, state what the paper would need to be accepted there (for example a more general theorem for EC, or a benchmark release for NeurIPS Datasets and Benchmarks) and how to restructure it within that venue's page limits.

## Task 4: Bibliography

- Verify every entry in the reference list against its primary source (authors, title, venue, year, volume, pages, DOI). Flag any error.
- List the references a referee would expect and we are missing, with full citations and one sentence on why each matters. Prioritise primary sources over surveys.
- Flag any reference that we cite for a claim it does not support.

## Rigor rules

- Every citation you give must be real and verifiable; give a DOI or stable URL. If you cannot verify a reference, say so and do not present it as fact.
- Separate what sources say from your own reasoning.
- Report disagreements between sources rather than smoothing them over.
- Quote the paper's exact sentence when you criticise it.

## Output format

1. Summary verdict (one paragraph) and a score as you would give at the recommended venue (strong reject to strong accept), with confidence.
2. Novelty: the closest works table and a plain statement of what is new.
3. Claims: numbered problems, each with the sentence, the issue, and a corrected wording.
4. Venue: the ranked list with deadlines and the requirements for the top two.
5. Bibliography: errors, missing references, misused references.
6. The three changes that would most improve the paper's chance of acceptance.
