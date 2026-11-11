# Reset pod launcher: internal review round 13 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 12 (`docs/revision/roster/{sol,astra}-reset-plan-r12.md`) rejected the launcher on three points; both seats closed the rest. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

Fixes:
- One price rule for the launcher and the watchdog. `podctl.price_of` accepts only a finite positive `costPerHr`; missing, null, zero, negative, NaN, infinite or unreadable is unknown. `podctl.record_price NAME ID` (CLI `record-price`) raises the rate in `NAME.acct` to the observed price, or, when the price is unknown or the listing fails, writes `NAME.unpriced`. `reset_pod.sh` uses it after a creation (a timeout of the call also writes `NAME.unpriced`); an unknown price still fails the price check ("PRICE unknown").
- The watchdog calls `record_price` for every pod before it deletes it, so a late pod's price enters the bound. If `NAME.unpriced` exists, the watchdog prints "UNRESOLVED BILLING ... check the Runpod console" and no "final spend bound". The launcher cleanup sets UNRESOLVED BILLING when `NAME.unpriced` exists.
- No 0.01 s floor: `list_pods` with a budget of 0 or less runs no command and returns None (fail-closed); `delete_verified` passes the exact remaining budget.

Tests: `test_podctl.py` + `test_runpod.py` 37 pass, including 14 new r13 tests (seen RED). One old test (`test_a_failed_listing_is_never_an_empty_list`) changed only its expected value, because the fake listing now carries a price.

Harness: 9 scenarios (the 7 of round 12, plus: null price ends "PRICE unknown" with UNRESOLVED BILLING in launcher output and watchdog log; a late pod at 9.0 USD/h after an ambiguous answer gives "at 9.0 USD/h" in the watchdog log). The harness is running now (about 2.5 h); the pod launch is gated on HARNESS OK as well as on this review.

Check: (1) each round-12 correction is closed; (2) new defects; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
