"""One creation request per call (internal review r10: no hidden retries). Usage: create_one.py NAME INDEX
INDEX selects one (flavor, cloud) combination; prints {"id": ..., "vcpu": ...} or {"id": "", "ambiguous": bool}.
Only a clear client refusal (HTTP 4xx other than 408/429) is unambiguous (podctl.classify_creation, r11); after an
ambiguous answer the launcher sends no further request."""
import json, sys
sys.path.insert(0, "/Users/oemer.demirel/Projects/touchstone/results/pods")
from runpod import api
from podctl import classify_creation
IMAGE = "runpod/base:0.6.2-cpu"
COMBOS = [(f, c) for c in ("SECURE", "COMMUNITY") for f in ("cpu5c", "cpu3c", "cpu5g", "cpu3g", "cpu5m", "cpu3m")]
name, i = sys.argv[1], int(sys.argv[2])
if not 0 <= i < len(COMBOS):
    print(json.dumps({"id": "", "ambiguous": False, "exhausted": True})); sys.exit(1)
f, c = COMBOS[i]
r, exc = None, None
try:
    r = api("POST", "/pods", {"name": name, "computeType": "CPU", "cloudType": c, "cpuFlavorIds": [f], "cpuFlavorPriority": "availability",
                              "vcpuCount": 16, "imageName": IMAGE, "ports": ["22/tcp"], "containerDiskInGb": 20, "env": {"OMP_NUM_THREADS": "1"}})
except Exception as e:
    exc = e
pid, amb = classify_creation(r, exc)
if pid:
    print(json.dumps({"id": pid, "vcpu": 16, "flavor": f, "cloud": c})); sys.exit(0)
print(json.dumps({"id": "", "ambiguous": amb})); sys.exit(1)
