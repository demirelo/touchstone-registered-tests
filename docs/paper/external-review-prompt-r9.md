# Fresh external review (paste this; attach every file listed under "Materials" separately)

You are an expert referee for a security-economics or multi-agent systems venue. You have not seen this paper before.
Review it as you would a real submission you must decide on: adversarial, specific, and fair. Do not be polite at the
expense of accuracy. A confident wrong claim is worse than a stated uncertainty.

The paper is "Checking Newcomers When Identities Are Free: Two Registered Tests of an Audit Rule" (`main.pdf`). It
studies a procurement market where a buyer can audit only a sample of jobs, and a banned provider can return at once
under a new identity. It proposes an audit rule, R3, that targets new identities, and reports two pre-registered
simulation tests: one against uniform-audit baselines and one against a verified-history comparator, C*.

First, list which files you could open and read. If a file did not open, say so and do not guess its content.

## Materials (attached separately)

1. `PROMPT.md`: this prompt.
2. `main.pdf`: the paper (27 pages).
3. Registration: `protocol-v2.yaml` (the locked protocol), `predictions-v2.md` (registered predictions and the scoring
   rubric), `revision-program-design.md` (design; section 9 gives estimands, decision rules, and scope).
4. Outputs of the tagged code: `report.md` (the report the frozen code wrote; large), `addendum.md` (labels and
   disclosures added after the report), `stability-result.json` (a re-evaluation with the registered configurations).
5. Inference audit: `audit.json`, `audit_v2.py`.
6. Exploratory analyses: `posthoc.json`, `posthoc_v2.py`, `lottery_seeds.csv`, `lottery_train.csv`.
7. Prediction scoring: `score_v2.py` (scorer), `test_scoring.py` (its tests; they need the repository to run, so read
   them for what they assert), `scoring.json` (the original numerical scoring), `eligibility.json` (per-cell inputs,
   traced ancestors, search flags, and status under three eligibility readings).
8. Process record: `operations-ledger.md` (what was run, when, and at what cost), `h4-family.py` and
   `h4-containment.md` (the sealed attacker family and how it was kept from development).

## Tasks

1. **Claims.** State the paper's main claims in your own words, in at most five lines. For each, say whether the
   evidence supports it as stated, supports a narrower version (give it), or does not support it.
2. **Correctness.** Check the headline numbers against the outputs. At minimum: the Q1 pooled classification and
   estimates, the Q2 factorial contrasts, the Q4 count of passing markets, the welfare and lottery efficiencies, and the
   prediction tallies in the eligibility table. Recompute what you can from the attached files and state each result
   as reproduced, not reproduced (with your value), or not checkable from the materials.
3. **Theory.** Check Corollary (uniform audits make the ban costless under free replacement) and Lemma (coverage of a
   replacement under R3) for correct statements, hidden assumptions, and whether the text claims more than they prove.
4. **Method.** Judge the registration (what was fixed before the outcomes, and what changed after), the attacker
   searches (are they strong enough to support "robust" or "equivalent" claims?), the statistics (margins, calibration,
   multiplicity, nominal versus calibrated intervals), the selection of C* (is the comparison fair?), and the
   separation of registered from exploratory results. Name any place where a post hoc choice could drive a conclusion.
5. **Novelty and related work.** Is the contribution new relative to probation and spot-checking work (credibility-
   based spot-checking, BOINC adaptive replication, cheap pseudonyms, audit games, costly verification)? Name missing
   prior work only if you can give a real, verifiable citation (DOI or stable URL); say so if you are unsure.
6. **Presentation.** Is the paper readable for the target venue? Say what to cut, move to a supplement, or rewrite,
   and where a reader would get lost. The paper is long (27 pages, many tables); say what a venue version should keep.
7. **Decision.** Give a score and an acceptance probability for each venue: WEIS 2027, AAMAS (main track), and ACM EC.
   For each, give your confidence and the single change that would move the score most.

## Rigor rules

- Quote the paper's exact sentence when you criticise it, with the page or section.
- Separate what the files say from your own reasoning and from what you could not check.
- Every number you report says where it comes from (file and field, or your computation).
- Every citation must be real and verifiable (DOI or stable URL).
- Do not reward or penalise the paper for its disclosed failures as such; judge whether the conclusions follow.

## Output format

1. Files read (one line each, or a list of any that failed).
2. Summary verdict (one paragraph) with scores per venue.
3. Claims table (claim, evidence, verdict).
4. Correctness checks (table: item, paper value, your value or "not checkable", source).
5. Theory and method problems, ranked by severity. For each: the quote, the problem, its effect on the conclusions,
   and the exact fix. Label each fix **text only**, **analysis on existing records**, or **needs compute**.
6. Novelty and missing related work.
7. Presentation and the venue version.
8. Decision table: venue, score (1 to 5), acceptance probability, confidence, what would move it.
