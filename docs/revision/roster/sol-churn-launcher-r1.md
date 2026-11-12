VERDICT: reject

CORRECTIONS:
1. docs/revision/churn/churn_pod.sh:116 — The deadlines ignore PRIOR. With PRIOR=3, the watchdog permits another 10.40 USD, so the arm’s bound becomes 13.40 USD. Subtract recorded prior spend from the remaining soft and hard allowances, or reserve the larger cumulative bound. Ruling 1 holds for a fresh launch only.

2. docs/revision/churn/churn_pod.sh:143 — Attempt accounting starts after creation returns; `--started` uses `a0`, set after the price check at line 151. Both omit potentially billed time. Record a conservative start immediately before each creation request. Use it for deleted-attempt charges and the current driver’s `--started`. Ruling 2’s formula is correct, but its timestamps undercount.

3. docs/revision/churn/churn_pod.sh:184 — A gate-stage cap refusal becomes `GATE FAILED`, then “not bit-identical” at line 209. A read-only reproduction confirmed this with PRIOR=7.90. Apply the cap-refusal classification to `c_gate.log` and report `STOPPED BEFORE gate (cap, driver admission)`. Ruling 3 is incomplete.

4. docs/revision/churn/churn_pod.sh:176 — `/tmp/r_remote_$TAG.sh` collides with the reset launcher’s temporary script. Their different launch locks permit concurrent launches with the same TAG; either can upload the other’s script. Use a private temporary path that includes NAME and a unique suffix.

5. docs/revision/churn/test_churn_pod_harness.sh:116 — The new cap scenario supplies the final status text through `remote_tail`; it does not execute driver admission or log classification. Add tests for the generated remote script, gate cap refusal, prior/deleted-attempt accounting, and separate temporary paths. The saved log reports 16/16 passes; shell syntax and installed-copy equality pass. I did not rerun the file-writing harness under the read-only constraint.

CONFIDENCE: 0.95.