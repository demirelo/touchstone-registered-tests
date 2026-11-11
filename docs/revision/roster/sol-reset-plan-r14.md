VERDICT: reject

CORRECTIONS:
1. Closed — `podctl.py:81`, `podctl.py:108`, `podctl.py:138`, `reset_pod.sh:84`: reconciliation records prices; invalid prices mark billing unresolved; existing unknown-price markers suppress bound messages. The timeout fixes at `podctl.py:38,58,61` remain present.
2. Blocker — `reset_pod.sh:72,115,120`: retries retain the previous pod’s `cph`. If a signal interrupts a later attempt before its price check, cleanup skips `record-price` and deletes the new pod. An offline reproduction of the actual cleanup function confirmed this sequence. Reset the price state for each attempt or always record the current pod’s price before cleanup deletion.
3. Blocker — `reset_pod.sh:75,85`: cleanup reconciliation can raise `.acct` without updating the shell’s `rate`. A reproduced 9.0 USD/h pod updated `.acct`, but the launcher retained 0.7 USD/h for “spend bound so far.” Read the recorded maximum before printing.
4. Blocker — `podctl.py:129-131`: concurrent price records can lower the stored maximum. An in-memory interleaving wrote 9.0, then overwrote it with 1.0 from an earlier read. Protect the complete accounting update with a shared lock.
5. Validation — `test_podctl.py:232`, `test_reset_pod_harness.sh:78`: all 39 supplied cases passed with memory-only substitutes; both shell syntax checks passed. The tests miss the defects above. HARNESS OK remains required and was not verified in this review.

CONFIDENCE: 0.99.