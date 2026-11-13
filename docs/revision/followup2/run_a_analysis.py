# Plan step 3 (runner-up-plan.md): analysis on the Mac from the retrieved records. Calls the driver's own analysis()
# at dc296bd; the driver's --site mac path refuses because the pod reset gate binds the pod's numerical stack.
import json, sys
from pathlib import Path
sys.path.insert(0, "docs/revision/followup2")
import runnerup_v2 as RU
out, src, report = sys.argv[1:4]
res = RU.analysis(out, src, json.loads(Path(report).read_text()))
Path(out, "analysis.json").write_text(json.dumps(res, indent=1, sort_keys=True))
print(json.dumps(res.get("D2+H3", {}).get("expectation")))
