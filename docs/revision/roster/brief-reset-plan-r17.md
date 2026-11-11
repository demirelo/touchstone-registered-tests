# Reset pod launcher: internal review round 17 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Round 16 (`docs/revision/roster/{sol,astra}-reset-plan-r16.md`) rejected the launcher. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`; plan step 4 in `docs/revision/reset-experiment-plan.md`.

Round-16 items:
1. Credits (Sol 1, Astra 1): the API exposes no transaction history (GraphQL schema lookup is refused), so absence of credits cannot be verified by code. `podctl.spend` refuses a balance that rose, and its record states "valid only if no deposit or credit was added between <bal0 time> and <read time> (check the Runpod billing page)". Plan step 4: the author confirms on the billing page before the record enters the ledger. This is a stated, author-verified condition, like the 30-minute late-pod assumption.
2. Watchdog clocks (Sol 2, Astra 2): wall time only for the hard deadline; the settle time and deletion budgets use `mono` (default `time.monotonic`). Test: a +3600 s wall jump after 30 s does not shorten the 1800 s settle.
3. Records across launches (Sol 3, Astra 4): a launch is refused while `NAME.bal0` exists without `NAME.spent`, before any file changes; `podctl.py spend` writes `NAME.spent`; the next launch moves bal0, wdend, spent and attempts to `spend_records/NAME.<time>/`. A launch with no request moves its bal0 there as unused.
4. Remote failures (Sol 4, Astra 3): preparation runs under `set -e` with no masking pipe; start uses `chmod ... &&`; the run counts as started only when the remote log's first line "== remote started" is seen.
5. Unchecked writes (Astra 5): bal0 and the pending marker are written and read back before any request.
6. Rounding (Sol 5, Astra 7): Decimal with ROUND_CEILING to the cent. Test: 10 -> 9.989999999 gives 0.02.
7. Harness (Sol 6, Astra 6): a filtered run prints "HARNESS PARTIAL" (exit 2); OK needs all 13 scenarios. Every end state is a full anchored line; refusal scenarios check their full message start. New: an unrecorded previous spend refuses the launch and keeps its baseline.

Tests: 49 pass (r17 tests seen RED). Harness: smoke of 3 instant scenarios gave PARTIAL as designed; the full 13-scenario run is going (about 3 h). The launch is gated on "HARNESS OK (13 of 13 scenarios)" and this review.

Check: (1) each round-16 item is closed; (2) new defects in one pass; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
