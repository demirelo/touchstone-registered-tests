"""One creation request per call (internal review r10: no hidden retries). Usage: create_one.py NAME INDEX
INDEX selects one (flavor, cloud) combination; prints {"id": ..., "vcpu": ...} or {"id": "", "ambiguous": bool}.
Only a clear client refusal (HTTP 4xx other than 408/429) is unambiguous (podctl.classify_creation, r11); after an
ambiguous answer the launcher sends no further request. Runpod v2 (2026-11-21): only HTTP 201 with an id is a pod; a 202
answer is a queued request whose id is not a pod id, so it is ambiguous (it may still become a pod)."""
import json, sys
sys.path.insert(0, "/Users/oemer.demirel/Projects/touchstone/results/pods")
from runpod import _http
from podctl import classify_creation
IMAGE = "runpod/base:0.6.2-cpu"
COMBOS = [(f, c) for c in ("SECURE", "COMMUNITY") for f in ("cpu5c", "cpu3c", "cpu5g", "cpu3g", "cpu5m", "cpu3m")]
name, i = sys.argv[1], int(sys.argv[2])
if not 0 <= i < len(COMBOS):
    print(json.dumps({"id": "", "ambiguous": False, "exhausted": True})); sys.exit(1)
f, c = COMBOS[i]
status, r, exc = None, None, None
try:
    status, r = _http("POST", "/pods", {"name": name, "cloud": c, "cpu": {"id": f, "vcpuCount": 16}, "image": IMAGE,
                                        "ports": ["22/tcp"], "disk": 20, "env": {"OMP_NUM_THREADS": "1"}, "startSsh": True})
except Exception as e:
    exc = e
# Classified by the HTTP status (review r1): only 201 with a non-empty string id is a pod; an HTTP error status goes to
# the r11 rule; every other answer (200, 202 queued, 3xx, a body "error" on a success status, a non-string id) is ambiguous.
if exc is None and status == 201 and isinstance(r, dict) and isinstance(r.get("id"), str) and r["id"]:
    pid, amb = r["id"], False
elif exc is None and isinstance(status, int) and status >= 400:
    pid, amb = classify_creation({"error": status}, None)
else:
    pid, amb = "", True
if pid:
    print(json.dumps({"id": pid, "vcpu": 16, "flavor": f, "cloud": c})); sys.exit(0)
print(json.dumps({"id": "", "ambiguous": amb})); sys.exit(1)
