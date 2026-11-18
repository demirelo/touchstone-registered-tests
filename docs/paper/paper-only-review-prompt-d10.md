# Referee review of the paper only (draft 10)

You are an expert referee for a security-economics or multi-agent systems venue (WEIS, AAMAS, ACM EC). Review the
attached paper, `submission-anon-d10.pdf` (38 pages; the main text ends on page 18, then the appendix). Review **only
the paper**: you have no code, records or earlier reviews, and you should not ask for them. Judge whether the paper, as
written, supports its own claims.

The paper studies a procurement market in which a buyer can audit only a sample of delivered jobs and a banned provider
can return at once under a new identity. It proposes R3, an audit rule that checks new identities first and then keeps
targeting the newest ones, and reports two pre-registered simulation tests against uniform audits (B3) and a
verified-history comparator (C*), plus exploratory follow-ups specified after the report: identity replacement disabled
(Section 9) and honest identity churn at four rates (Section 10).

Be adversarial, specific and fair. A confident wrong claim is worse than a stated uncertainty.

## Tasks

1. **Main claims.** List the paper's main claims in your own words. For each, say whether the evidence in the paper
   supports it, partly supports it, or does not, with the page and the table or figure.
2. **Registered versus exploratory.** Check that every exploratory result is labelled as such where it appears, that no
   exploratory result is presented as registered, and that the registered decisions are reported unchanged. Check the
   title and abstract in particular.
3. **Internal consistency.** Check that the same quantity has the same value and the same meaning in the abstract, the
   introduction, Sections 8 to 12, the tables and the appendix. Report every mismatch with both pages.
4. **Comparative and universal words.** Check each "falls", "rises", "reverses", "every", "all", "only", "never" and
   "survives" against the table it describes, for both search versions (frozen and doubled) where the paper gives both.
5. **Statistics and inference.** Are the intervals described correctly (what they condition on, what they omit)? Are the
   sign counts, market-level intervals and paired changes interpreted within their limits? Is any post hoc choice able to
   drive a conclusion?
6. **The churn result (Section 10).** Is the mechanism described without causal claims the design cannot carry? Are the
   C* and B3 comparisons kept apart? Is the scope (one comparator under churn, six markets, flagged searches) stated
   where the claims are made?
7. **Theory.** Check the stated results (Lemma 1, Corollary 1, Lemma 2, Proposition 1, Theorem 1 in the appendix)
   against their assumptions and proofs. Say what each result does and does not establish for the simulated process.
8. **Novelty and related work.** Is the contribution stated accurately against the cited work on credibility-based
   checking, adaptive replication and cheap pseudonyms? Name missing work only with a verifiable citation.
9. **Presentation.** Is the centre of the paper clear early? What should be cut, moved to the appendix, or rewritten?
   Is the abstract accurate and short enough?
10. **Decision.** For WEIS 2027, AAMAS (main track) and ACM EC: a score from 1 to 5, an acceptance probability, your
    confidence, and the single change that would move the score most.

## Rigor rules

- Quote the paper's exact sentence when you criticise it, with the page.
- Separate what the paper says from your own reasoning and from what you cannot check without the records.
- Every number you report says where in the paper it comes from (page, table, figure) or that it is your computation.
- Every citation you add must be real and verifiable (DOI or stable URL).
- Do not reward or penalise the paper for its disclosed failures as such; judge whether the conclusions follow.

## Output format

1. Your model id (one line).
2. Summary verdict (one paragraph) with the three scores.
3. Main claims table: claim, support (supported / partly / not), evidence (page, table or figure), comment.
4. Problems ranked by severity. For each: the quoted sentence and page, why it is a problem, and an exact fix, labelled
   **text only**, **needs analysis of existing results**, or **needs new runs**.
5. Theory check.
6. Presentation and length.
7. Decision table: venue, score, acceptance probability, confidence, what would move it.
