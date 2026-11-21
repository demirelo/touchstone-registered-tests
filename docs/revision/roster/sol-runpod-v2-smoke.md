VERDICT: accept-with-caveat
CORRECTIONS:
1. `docs/revision/followup3/rep_pod.sh:301`; `results/pods/podctl.py:127` — The smoke run checked price after SSH readiness. The launcher checks price immediately after creation. Thus, immediate availability of v2 `cost`, mapped to `costPerHr`, remains unverified. A missing or null value would cause deletion and abort. No failure was observed. If this occurs, add bounded price polling within the existing deadlines; retain the price ceiling and deletion checks.
2. `docs/revision/followup3/rep_pod.sh:252`, `:283`; `results/pods/podctl.py:65`, `:221` — Reconciliation and watchdog loops were not exercised live. They consume `id` and `name`, both present in the smoke listing. No additional field mismatch or correction was found.
3. `docs/revision/followup3/rep_pod.sh:312`, `:398`, `:418`, `:429` — Full preparation, remote execution, and monitoring were not exercised. Their transport uses `ssh.direct.host` and `ssh.direct.port` through `GET /pods/{id}`, which the smoke run verified. They do not consume the missing list SSH fields. No correction is required. The evidence supports relaunching pod 1 with the existing guards.

CONFIDENCE: 0.95