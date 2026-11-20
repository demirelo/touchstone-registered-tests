VERDICT: reject

CORRECTIONS:

1. `commitment.py:20–32`: Require the runner-up recheck record read by `runnerup_v2.runner_up_cred` (`followup2/runnerup_v2.py:36–54`). A manifest builds successfully without this parameter source. Round-1 correction A1 remains incomplete.

2. `rep_collect.py:235–239`: Validate record stages, dependency sets and hashes, and the doubling record’s contents. An in-memory example with a wrong evaluation stage, absent dependencies, and a doubling record without held-out results was scored with zero unscorable cells. Round-1 correction C1 remains incomplete.

3. `rep_collect.py:225–226,254–264`: Check the gate’s provenance and require an identical measured round-1 comparison for each continued winner. Restrict accepted continuation statuses. An unknown status with no comparison entered the primary set as “unresolved”; a gate from another job passed.

4. `rep_collect.py:243,269–271,310–312`: Validate frozen and continued diagnostics before scoring or reuse. Check provenance, ordered seeds, winner knobs, bin structure, and finite counts. Diagnostics from another job with the wrong seeds supplied primary audit counts. This repeats the diagnostics-validation lesson and can change expectation 5.

5. `replication_analysis.py:158–171,179–190`: Produce seed-bootstrap intervals for absolute contrasts at p = 0. They currently return `None`. Also compute positive-rate absolute intervals when their cells exist but baseline cells are missing; only paired changes require the baseline.

6. `rep_collect.py:158–184,314–315`; `followup2/convergence_v2.py:300`: Fix lost-worker handling on resume. An existing cost-stopped record masks a worker death; the reproduced exit was 3 instead of 5. A lost diagnostics worker also returns 5 without writing the restart estimate required by `rep_pod.sh:374–375`. Add checks for both paths.

7. `rep-launcher-notes.md`, “Rulings”: Accept rulings 1–7, 9, and 11. Correct enforcement for rulings 8 and 10 as specified above. Accept ruling 12: external Mac launcher helpers are outside the stated driver-import requirement. The 65 Python tests pass; shell syntax passes. The supplied harness log reports 46/46, and its harness and launcher hashes match the current files. These checks do not cover the failures reproduced above.

CONFIDENCE: 0.97.