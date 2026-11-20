VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup3/rep_collect.py:165–173` — H2 still checks round-1 winner fields only for finiteness. Changing the gate and continuation comparison’s knobs and mean to unrelated values (`999`) left `gate_ok=True`, `round1_mismatch=False`, and the continued winner in the primary set. Check the comparison against this cell’s current doubling record and round data; zero-difference summary fields alone do not establish identity.

2. `docs/revision/followup3/rep_collect.py:279–283` — H1/H4 do not handle malformed value types. A scalar `heldout.gain=0.5` raises `TypeError` during collection instead of retaining the frozen winner. Scalar seeds and normalizers also raise errors. Check container types before iteration or length checks. Invalid base records must become unscorable; invalid continuation records must take the prescribed fallback or rerun.

3. `docs/revision/followup3/rep_collect.py:227–235` — H1’s rerun rule remains incomplete. An unknown saved status raises `SystemExit` before validation and set-aside; an in-memory probe made zero worker calls. Route invalid statuses through set-aside and rerun, while preserving the mandatory stop for a measured round-1 mismatch. Update the existing test that requires this refusal.

4. `docs/revision/followup3/rep_collect.py:469–477` — Ruling 8 unnecessarily requires valid frozen diagnostics before using valid continued diagnostics. Removing only the frozen binding removed the primary audit count `(5, 100)`, although the continued winner and its diagnostics remained valid. Check continued diagnostics independently; require frozen counts only when the primary winner is frozen.

5. `docs/revision/followup3/rep-impl-r3-response.md:H1,H2,H4,H8`; `rep-launcher-notes.md:Rulings 8,10` — Correct completion claims after these fixes. All 128 tests passed, and the supplied 47/47 harness hashes match. Those checks do not cover the reproduced failures above.

CONFIDENCE: 0.97.