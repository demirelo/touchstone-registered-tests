# Review brief: live smoke test of the Runpod v2 helper port

You are a read-only reviewer. Return exactly: `VERDICT: accept | accept-with-caveat | reject`, then `CORRECTIONS:` (numbered,
each with file:line, the concrete failure, and a fix), then `CONFIDENCE: <0-1>`. No other sections.

## Context

You accepted the port in round 3 (`docs/revision/followup3/runpod-v2/`, `runpod.py`, `create_one.py`, tests). The installed
files in `results/pods/` are byte-identical to those review copies (checked with `diff -q`). The author approved one
throwaway smoke pod. It ran on 2026-11-21 with `docs/revision/followup3/runpod-v2/smoke.sh`; its full output is
`docs/revision/followup3/runpod-v2/smoke-2026-11-21.log`.

What the smoke run exercised: preflight `runpod.py list` and `balance`; one `create_one.py ts-smoke 0` request (HTTP 201,
cpu5c SECURE, 16 vCPU); `runpod.py get` until a direct SSH endpoint appeared (20 s); `runpod.py list`; `runpod.py ssh`,
`push`, `pull`; `runpod.py delete`; a listing without the pod; `get` returning 404.

One observation for you to judge: in `list` output the pod has `publicIp: null` and `portMappings: {}`, while `get` shows
the address and port. The v2 list endpoint apparently omits `ssh.direct`. The launcher (`docs/revision/followup3/rep_pod.sh`)
and `results/pods/podctl.py` read only `id`, `name` and `costPerHr` from `list` (grep for `publicIp`, `portMappings`); SSH
and rsync resolve the endpoint through `GET /pods/{id}` (`runpod.py` `target()`).

## Question

Does this live evidence, together with your round-3 review, support relaunching replication pod 1 with these helpers?
Name any launcher path (`rep_pod.sh` lines 252, 283-320, 398-430; `podctl.py`) that the smoke run did not exercise and
that could still fail on a v2 field difference, with the concrete field. Do not repeat round-3 issues already fixed.
