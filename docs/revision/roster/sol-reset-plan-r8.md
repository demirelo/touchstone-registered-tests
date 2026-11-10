VERDICT: reject
CORRECTIONS:
1. `results/pods/reset_pod.sh:69–70`: Cleanup deletes the pod after three failed retrieval or verification attempts, even before the hard deadline. An inert test confirmed this path. After RUN OK, retain the pod and retry retrieval until both inventories pass or the hard deadline requires deletion.
2. `results/pods/reset_pod.sh:82–93`: The watchdog starts after price validation and all SSH readiness attempts. Failures before that point enter cleanup without a watchdog. Start the watchdog immediately after receiving each pod ID, with a deadline that also covers readiness and failure cleanup.
3. `results/pods/reset_pod.sh:85`: Deadline arithmetic applies the current pod’s price to all elapsed time, including earlier attempts. A cheaper replacement can therefore exceed the spending limit. Accumulate spending for each attempt, or calculate deadlines conservatively with MAXCPH.
4. `results/pods/reset_pod.sh:108–111`: The reproduction gate starts without checking STOP or the soft deadline. Add the same deadline check before the gate that precedes the later stages.

CONFIDENCE: 0.98.