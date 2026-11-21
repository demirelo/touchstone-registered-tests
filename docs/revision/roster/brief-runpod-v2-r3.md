# Review brief: Runpod v2 port of the Mac pod helpers (round 3)

You are a read-only reviewer. Return exactly: `VERDICT: accept | accept-with-caveat | reject`, then `CORRECTIONS:` (numbered,
each with file:line, the concrete failure, and a fix), then `CONFIDENCE: <0-1>`. No other sections.

## Context

On 2026-11-21 the churn replication launch (`docs/revision/followup3/rep_pod.sh`, frozen in the published manifest
`experiments/v2/replication-manifest.json`) failed before any creation request: Runpod retired `rest.runpod.io`
(NXDOMAIN, also at 1.1.1.1). No pod was created. The Mac helpers `results/pods/runpod.py` and `create_one.py` (outside
the manifest and the repository) must move to `https://api.runpod.io/v2`. The launcher and `podctl.py` cannot change, so
the port must keep the helpers' output contract exactly.

Files (copies for review, in `docs/revision/followup3/runpod-v2/`):
- `runpod.py`, `create_one.py`: the port. `old/runpod.py`, `old/create_one.py`: the v1 originals (diff them).
- `podctl.py` (unchanged; reads `runpod.py list|delete|balance` and calls `classify_creation`), `test_podctl.py`,
  `test_runpod.py` (unchanged), `test_runpod_v2.py` (new, 30 tests; HTTP faked, no request reaches Runpod).
- The launcher's uses: `rep_pod.sh` lines 252, 283-320, 398-430 (`runpod.py ssh|pull`, `podctl.py price|reconcile`,
  `create_one.py NAME INDEX`).
- The v2 contract: `https://api.runpod.io/v2/openapi.json` is not reachable from your sandbox; the facts below were read
  from it on 2026-11-21:
  - `GET /v2/pods` -> 200 `{pods: [Pod], pagination: {nextCursor: string|null, hasNextPage: bool}}`; query `cursor`.
  - `Pod` requires id, name, status (PROVISIONING|STARTING|RUNNING|EXITED|ERROR|TERMINATED), cost (number), ssh
    `{proxy, direct}`, each `null` or `{host, port, username, command}`; `direct` is null unless `22/tcp` is in ports and
    the pod runs; cpu `{id, vcpuCount, memory}`.
  - `POST /v2/pods` -> 201 Pod, or 202 a queued request `{id, status, podId, failureReason, ...}` whose id is not a pod
    id; 400/401/403/404/409/413/422/429 errors. Body: name, cloud (SECURE|COMMUNITY), cpu `{id, vcpuCount}`, image,
    ports, disk, env, startSsh (SSH keys reach the pod only with startSsh), optional queue (not sent).
  - `DELETE /v2/pods/{id}` -> 204 with no body; 404; 409 for cluster pods.
  - CPU catalog ids are unchanged (cpu3c, cpu3g, cpu3m, cpu5c, cpu5g, cpu5m).
  - Live read-only checks: the staged `runpod.py list` returned `[]` with exit 0; `get nosuchpod` returned the 404
    error dict; the account's registered SSH keys include the local `runpodctl-ssh-key`.

## What to check

1. `list` fails closed: no answer shape, status, network error or pagination state may print a list that hides a pod
   (podctl's reconcile, delete_verified and watchdog treat the printed list as the truth). Is dropping TERMINATED pods
   safe (they no longer bill)? Any shape that could make a live pod disappear?
2. Creation classification: only 201 with an id is a pod; 202 and any other non-error status are ambiguous; HTTP errors
   keep the r11 rule (4xx other than 408/429 unambiguous). Any path that returns a non-pod id as a pod id, or that calls
   an ambiguous answer unambiguous?
3. The old field contract: id, name, desiredStatus, publicIp, portMappings["22"], costPerHr, vcpuCount. `podctl.price`
   reads costPerHr from the list; `rep_pod.sh` refuses a price outside (0, MAXCPH] and checks vcpu. Is `cost` the right
   per-hour price field? Is the port the right one for ssh and rsync?
4. `ssh`/`rsync` without a direct endpoint return 255 (the launcher's readiness loop retries for 240 s). Correct?
5. Anything the tests miss that a live pod would show (field types, a pod listed before its ssh block exists).

A smoke pod (create, list, get, ssh echo, delete, list) runs after this review and before the real launch.

## Round 3

Responses: `docs/revision/followup3/runpod-v2/r1-response.md` (A-C) and `r2-response.md` (D, E). Earlier reviews:
`docs/revision/roster/{sol,astra}-runpod-v2-r{1,2}.md`. Check that D and E are fixed and complete, that A-C still hold,
and that nothing else hides a live pod or turns an ambiguous creation into a clear one.
