VERDICT: reject

CORRECTIONS:
1. `podctl.py:163`, `podctl.py:185`, `reset_pod.sh:58` — Record isolation remains incomplete. A repeated spend check can read the old baseline, overlap a new launch, then write the old spend into the new launch’s `.spent`. An in-memory reproduction confirmed this bypasses the next unrecorded-spend check. Serialize spend recording with archival and baseline replacement, or bind records to immutable launch IDs.
2. `podctl.py:185`, `reset_pod.sh:57` — A failed spend write can leave an empty `.spent`, which the launcher accepts because it checks only existence. An in-memory disk-failure simulation confirmed this. Write and close a temporary record successfully before atomic publication; validate the completed record before permitting reuse. Add regression tests for this failure and the race above.
3. `test_reset_pod_harness.sh:116` — Full harness verification remains pending. Keep the pod blocked until the corrected launcher produces `HARNESS OK (13 of 13 scenarios)`. The partial smoke run does not close this gate.

CONFIDENCE: 0.98.