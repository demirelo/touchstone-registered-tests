VERDICT: reject

CORRECTIONS:

1. `commitment.py:24–34,106–115`: A1 remains incomplete. Require the runner-up recheck record read by `runnerup_v2.LOG` and `churn/churn_memory.py`, which executes production preflight tasks. Import scanning misses both. Check Git return codes: an invalid all-zero commit currently produces no freeze problems.

2. `rep_collect.py:237–239`: C1 remains incomplete. Validate record stages, IDs, dependency sets/hashes, doubling contents and flag consistency. An in-memory check accepted a doubling record containing only provenance and `incomplete=False`.

3. `rep_collect.py:151–174,225–226,254–275`: Validate saved continuation status, rounds and each cell’s exact comparison before reuse or scoring. Require gate evidence from the expected job and run before primary analysis, including an all-unflagged run. Checks accepted an unknown continuation status without its own comparison, using a foreign gate; primary analysis also remained available without any gate.

4. `rep_collect.py:269–271,310–315`; `rep_pod.sh:372–377`: Validate diagnostic provenance, ordered seeds and winner knobs before reuse/scoring. A diagnostic worker loss returns 5 without writing its restart estimate, so the launcher fails or reads a stale estimate. Add a diagnostic-loss test through both layers. This repeats the lesson requiring each exit code to work across layers.

5. `replication_analysis.py:158–190`: C3 remains incomplete. Add absolute-contrast seed intervals at p=0; both market and pooled intervals currently return `None`. Compute positive-rate absolute intervals independently of baseline availability. Do not report a five-degree-of-freedom t interval for an incomplete market sample.

6. `rep_v2.py:390`; `rep_pod.sh:93`: Persist reduced continuation-worker limits across restarts. Check x86 architecture in pod 2’s bundle guard before provisioning; it currently checks only Linux, although the driver later checks both.

7. `rep-launcher-notes.md`, “Rulings”: Accept 1–6 and 9. Correct 7 through item 6, 8 through item 4, 10 through items 1–4, and 11 through item 6. Accept 12 as a literal exclusion from the manifest’s imported-helper scope, with a caveat: launcher self-verification does not verify external Mac helpers. Their correctness remains outside this review’s verified coverage.

8. `rep-impl-r1-response.md`, A1/B4/C1/C3/C4: Mark these corrections incomplete until the above checks pass. All 65 existing Python tests passed. Shell syntax passed; the 46/46 harness log hashes match. The harness and documented Mac smoke chain were not rerun.

CONFIDENCE: 0.97.