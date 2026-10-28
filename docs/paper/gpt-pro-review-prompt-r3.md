# Review prompt for GPT Pro, round 3 (paste this; attach the files listed under "Materials")

You are a senior referee and area chair with expertise in mechanism design (costly verification, repeated games, procurement), algorithmic game theory and multi-agent systems, security economics (Sybil and whitewashing, audit games), and empirical methodology (pre-registration, adversarial evaluation). This is your third review of this project. Be adversarial and specific. Do not soften findings. Give numbers where we ask for numbers, and say how confident you are.

## Context

In round 2 you reviewed paper draft 8 and the design of the second registered evaluation (design draft 6). Your verdict: draft 8 reject at AAMAS (2/5, confidence 4/5); 3/5 if the second evaluation ran as designed with favourable results; 4/5 (weak accept) with your before-lock fixes and favourable results; EC 1/5 now, at most 2/5 after. You wrote: "I would not lock the current protocol."

Since then:

- We checked every round-2 finding (`review-r2-triage.md`) and wrote **design draft 7** (`revision-program-design.md`), which takes your design findings D1 to D18. Two of our own reviewers accepted it.
- We implemented draft 7 in code and ran the **benchmark** that the design requires before any paid tuning (`benchmark-decision.md`). The measured cost is higher than the design estimate. By the design's own rule, the decision is the two-market development branch with **three cuts**, 49.25 USD in total. That needs the author's written approval, which **has not been given**.
- **Nothing is registered yet.** No tuning has run, H4 is not written, and no fresh market exists. This is still the last point where a design change costs nothing but money.
- The paper is still draft 8. Your round-2 text findings (T1 to T8, the bibliography) wait until the evaluation results are in.

The author must now choose between approving the cut plan, paying more to keep cut items, or stopping. The author wants your judgement of the paper's chance of publication under each choice, not only a list of defects.

## Materials (attached)

1. `PROMPT.md`: this prompt.
2. `main.pdf`: the paper, draft 8 (unchanged since round 2).
3. `review-r2-triage.md`: our triage of your round-2 review, with each finding, our check, and the action.
4. `revision-program-design.md`: **design draft 7** of the second evaluation. Section 14 maps each of your round-2 findings to the section that answers it.
5. `h4-brief.md`: the revised brief for the sealed, independently authored attack family. The author of H4 now reads the frozen defenders (your D2).
6. `benchmark-decision.md`: the measured costs, the decision, each cut with its cells and saving, and the four options. `decision.json`, `cost_table.json` (totals for no cuts, three development markets), and `timings.json` (measured seconds per task kind on 16 vCPU) are the raw records.
7. `review-response.md`: our triage of your round-1 review.
8. `reset-deterrence.md`, `checks-2026-10-21.md`: the theory with proofs and its pre-stated checks.
9. `final-evaluation-README.md`, `robustness-results.md`, `amendments/`: the first registered evaluation, its exploratory robustness study, and its four amendments.
10. `citations.md`: our verification log for every reference.

## Constraints (so that your suggestions are feasible)

- **Compute:** CPU simulation on rented pods at 0.56 USD per hour for 16 vCPU. The author will consider up to about 55 USD in total. If a suggestion costs more, say what it would replace.
- **Stated non-goals:** no LLM attackers, no change to the market model, no rule outside the admissible class, no population-level claim about all markets. If a non-goal makes the paper unacceptable, say so.
- **The first evaluation stays as registered.** The paper reports both evaluations.

## Task 1: Follow-through on round 2 (design draft 7)

For each design finding D1 to D18 in `review-r2-triage.md`, judge whether design draft 7 fixes it. Answer fixed, partly fixed, or not fixed, and quote the sentence in the design. Then list any new defect that draft 7 introduced: an overclaim, a forking path (a place where an outcome could still choose a cell, a threshold, or a reported number), an estimand that does not match its decision rule, or an attack that a skeptical referee would try first and that the design does not cover.

Answer plainly: **would you now lock this protocol?** If not, give the smallest set of changes that would make you lock it.

## Task 2: The cut decision (most important)

Read `benchmark-decision.md`. For each option:

- **A.** Approve as decided: cuts 1 to 3, total about 50 USD.
- **B.** Keep everything: raise the evaluation cap before the lock, total about 55 USD.
- **C.** Keep H4 on fresh markets only: change the cut order before the lock, total about 52.4 USD.
- **D.** Stop before the lock.

Answer:

1. How does each cut change what a referee can conclude? Weigh especially cut 2: without H4 on fresh markets, the independently authored attack covers only the headline market. Does that reopen your round-2 point that the authors' own attacks may be too weak?
2. Is the fixed cut order of design 8.2 the right one, given these measured savings? Cut 1 saves only 0.39 USD but comes first. Would you reorder, and why?
3. Is any other saving available that costs a referee less than these cuts (for example fewer doubling checks, fewer evaluation seeds on some blocks, or a smaller cross-evaluation)? Price it from `timings.json` and `cost_table.json` where you can, and say which numbers are your estimates.
4. Is the two-market development branch (tuning on the headline market and `dev0` only, not `dev1`) a weakness a referee would raise?
5. Your recommendation: A, B, C, D, or a variant, in one sentence, with the reason.

## Task 3: Publication chance

Give calibrated probabilities, as numbers, with a one-line reason each. Treat the evaluation as not yet run.

1. Your score now (draft 8 plus design draft 7, no results), with confidence.
2. For each option A, B, C: the probability of acceptance at (a) AAMAS main track, (b) a strong workshop or a specialist venue of your choice (name it), and (c) EC or another top venue of your choice (name it). Each probability should cover both favourable and unfavourable results, as they would come out of the registered protocol.
3. Which result patterns of Q1 to Q4 would move each probability most, and by how much. Name the pattern that leaves the paper unpublishable at every venue, if one exists.
4. What a negative or null result would be worth. Is the registered design strong enough that a null on Q1 (C* versus F111) is still a publishable finding? At which venue?

## Task 4: Venue and timing

Re-rank the venues for the paper as it will be after the second evaluation, with each venue's next deadline after October 2026. Verify the dates and give the source. The evaluation needs about three to five weeks after the lock. Say which deadline is realistic.

## Rigor rules

- Every citation you give must be real and verifiable; give a DOI or stable URL. If you cannot verify a reference, say so.
- Separate what sources say from your own reasoning.
- Quote the paper's or the design's exact sentence when you criticise it.
- For every probability, say what would change it. Do not give a range wider than 30 percentage points without saying why.

## Output format

1. Summary verdict (one paragraph): would you lock the protocol, your recommended option for the cuts, and your score now and expected after favourable results, each with confidence.
2. Round-2 follow-through: one line per finding D1 to D18 (fixed, partly fixed, not fixed), then the new defects, ranked, each labelled **before the lock** or **after**, with the cost in USD where it adds compute.
3. The cut decision: answers to items 1 to 5 of Task 2.
4. Publication chance: the table of probabilities (options A, B, C by venue tier), then items 3 and 4 of Task 3.
5. Venue: the ranked list with verified deadlines and a realistic target.
6. The three changes that would most improve the paper's chance of acceptance for at most 55 USD in total.
