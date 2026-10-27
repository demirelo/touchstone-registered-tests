# Review prompt for GPT Pro, round 2 (paste this; attach the files listed under "Materials")

You are a senior referee and area chair with expertise in mechanism design (costly verification, repeated games, procurement), algorithmic game theory and multi-agent systems, security economics (Sybil and whitewashing, audit games), and empirical methodology (pre-registration, adversarial evaluation). This is your second review of this paper. Be adversarial and specific. Do not soften findings.

## Context

In round 1 you reviewed draft 6 and recommended reject at AAMAS (2/5, confidence 4/5) and strong reject at EC. We checked every finding. `review-response.md` lists each one, our check, and the action. We split the actions in two:

- **Text actions** are applied in the attached draft 8: the reframing as an age-based instance of verification-based probation (Sarmenta, BOINC, customs, CrowdEval, probation monitoring), the corrected attribution (the killed predecessor without a priority phase already had most of the H3 effect), the threat model, the staged-registration wording, the claim corrections, a parameters appendix, 15 added references, and errata in the theory, checks, and final-evaluation documents.
- **Program actions** need new experiments. We designed a second registered evaluation for them (`revision-program-design.md`). **None of it has run yet.** Nothing is registered. The protocol v2 lock comes after development tuning and before any fresh market instance exists. This is the last point where a design change costs nothing.

If you still have your round-1 review, use it. If not, `review-response.md` lists every finding.

## Materials (attached)

1. `main.pdf`: the paper, draft 8.
2. `review-response.md`: our triage of your round-1 review.
3. `revision-program-design.md`: the design of the second evaluation (questions Q1 to Q4, rules, tuning, attack families, objectives, market instances and randomness, manifest and compute, protocol v2 estimands and decision rules, artifact, order of work).
4. `h4-brief.md`: the brief for the independently authored sealed attack family (Q3). A fresh model session writes the family from this brief into a sealed bundle; the authors do not open the bundle before the report.
5. `reset-deterrence.md` and `checks-2026-10-21.md`: the theory with proofs and its pre-stated checks (with errata).
6. `final-evaluation-README.md`: the first registered verdict, per-cell tables, run history, and erratum.
7. `robustness-results.md`: the 292-cell exploratory robustness results.
8. `amendments/`: the four amendment notes of the first evaluation.
9. `citations.md`: our verification log for every reference.

## Constraints of the second evaluation (so that your suggestions are feasible)

- **Compute:** CPU simulation on rented pods. Development cap 12 USD, evaluation cap 40 USD; any total above 40 USD needs the author's written approval. The estimate is about 50 USD. A suggestion that costs more must say so and say what it would replace.
- **Stated non-goals:** no LLM attackers, no change to the market model, no rule outside the admissible class (no fees or collateral before receipts), no population-level claim about all markets. If you think a non-goal makes the paper unacceptable, say so directly.
- **The first evaluation stays.** Its record, errata, and claims are not changed. The paper will report both evaluations.

## Task 1: Round-1 follow-through (draft 8)

For each round-1 finding marked "Text" in `review-response.md`, judge whether draft 8 fixes it. Answer fixed, partly fixed, or not fixed, and quote the sentence in draft 8. List any new overclaim or error that the revision introduced, with the exact sentence and a corrected wording.

## Task 2: Pre-registration review of the second evaluation (most important)

Read `revision-program-design.md` as a referee who will later read its results. Answer:

1. **Would it change your verdict?** For each question Q1 to Q4, say which result would move your score, in which direction, and by how much. Say which possible outcome would still leave the paper a reject.
2. **Q1 comparator.** Are the three credibility-based adaptations of Sarmenta and BOINC fair and strong? Is matching at one preselected parameter pair the right primary comparison, or does it favour one rule? Name the comparator you would demand and how to specify it within the admissible class.
3. **Q2 attribution.** Is the P, G, S factorial (priority phase, newest-first residual targeting, pacing), with separately searched attacks and with the attack held fixed, enough to identify each component's contribution? What would you add or cut?
4. **Q3 attack strength.** Are the state-conditioned family, the sealed independently authored family, the sabotage attacks, and the coalition scoring (total and worst member) strong enough? Name the attack a skeptical referee would try first and say whether the design covers it.
5. **Q4 replication.** Is the market neighbourhood, six fresh instances drawn after the lock from a block hash, enough to support the replication claim the design makes? Is the confirmatory label justified?
6. **Decision rules and forking paths.** Check the estimands, thresholds, multiplicity control, cuts, stop rules, and the order of work. Find any place where an outcome could still choose a cell, a threshold, or a reported number.
7. **The fix list.** Give a ranked list of changes, each labelled **before the lock** (it changes the protocol) or **after** (text or reporting only), with the cost in USD where it adds compute.

## Task 3: Novelty update

Search again for close prior work, by concept and not by our words, with special attention to anything published or posted in 2025 and 2026. Has the reframing as age-based verification-based probation placed the contribution correctly? State plainly what is new, what is incremental, and what is known, now and after the planned evaluation if it succeeds.

## Task 4: Venue and timing

Re-rank the venues for the paper as it will be after the second evaluation, with each venue's next deadline after October 2026 (verify the dates). The evaluation takes a few weeks after the lock. Say which deadline is realistic and what to cut or move to an appendix to fit that venue's page limit.

## Task 5: Bibliography

Verify every entry in the draft-8 reference list against its primary source (authors, title, venue, year, volume, pages, DOI), with special care for the 15 references added in draft 7. Flag errors, references cited for a claim they do not support, and references a referee would still expect.

## Rigor rules

- Every citation you give must be real and verifiable; give a DOI or stable URL. If you cannot verify a reference, say so and do not present it as fact.
- Separate what sources say from your own reasoning.
- Report disagreements between sources rather than smoothing them over.
- Quote the paper's or the design's exact sentence when you criticise it.

## Output format

1. Summary verdict (one paragraph): your score for draft 8 as it is, and the score you expect if the second evaluation runs as designed and its results are favourable, each with confidence.
2. Round-1 follow-through: one line per finding (fixed, partly fixed, not fixed), then new problems.
3. Second evaluation: answers to items 1 to 6 of Task 2, then the ranked fix list (before the lock or after, cost).
4. Novelty: the closest works and a plain statement of what is new.
5. Venue: the ranked list with deadlines and a realistic target.
6. Bibliography: errors, misused references, missing references.
7. The three changes that would most improve the paper's chance of acceptance.
