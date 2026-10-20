# Consensus record: exploratory attackers plan (2026-10-20)

Roster: Sol high (gpt-6.1-sol), Astra high (gpt-6-astra), Codex CLI, read-only, no paid APIs. Rule: qualified consensus.

Round 1: both REJECT v1 (honest points of X4 and X6 not honest under noise and scheduled resets; identity clock one round late; X6 reference ranked with coalition-cached scores; gross funding used as profit; bank provenance; seed allow-list because `final_eval` is null in the lock). Round 2: both REJECT v2 on the same three points (frozen `doubling_check` breaks X6 semantics; staggered-control arithmetic; X4 observation eligibility) plus Astra's dependency-complete pilot. Vote on v3: Sol accept (0.96), Astra accept (0.96); both checked the staggered schedule arithmetic (600 cases). Caveat from both: implementation and tests remain to be verified.
