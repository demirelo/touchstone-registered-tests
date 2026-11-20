#!/bin/bash
# Offline harness for rep_pod.sh (the churn replication's two pods; derived from test_followup2_pod_harness.sh) with
# podctl.py and fake runpod.py / create_one.py (no real pods). The fakes keep pods, pending (delayed) creations and stuck
# deletions in state.json under an exclusive lock (r15). Each pod scenario asserts: the pods left (0), the exact number of
# creation requests, the launcher exit status, the end state (an anchored pattern), that the watchdog ended by itself
# (unless the scenario expects it to stay, fail-closed) and released the launch lock, and, where stated, a watchdog log
# line, a launcher output line, and a line that must not appear (NOTOUT). The shared pre-pod path (guards, lock, creation,
# price, watchdog, deletion) is exercised with pod 1; pod 2 gets its own guards, RUN OK and end-state scenarios. The
# generated remote scripts of both pods are executed under a scratch root with a stub `uv` for every end state, with the
# real guards.py admission once, and the embedded verifier is run on prepared directories.
set -u; H=$(mktemp -d); cd $H; SRC=/Users/oemer.demirel/Projects/touchstone/results/pods
WT=/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79; LSRC=$WT/docs/revision/followup3/rep_pod.sh
python3 $SRC/case_end_check.py $LSRC || { echo "HARNESS FAILED (a case branch ends inside a comment)"; exit 1; }
sed "s#P=/Users/oemer.demirel/Projects/touchstone/results/pods#P=$H#; s#snapf=\"/Users/oemer.demirel/Projects/touchstone/results/pods/snap_#snapf=\"$H/snap_#; s#^PY=/opt/homebrew/bin/python3;#PY=$H/pywrap;#" $LSRC > rep_pod.sh
grep -q "^PY=$H/pywrap;" rep_pod.sh || { echo "HARNESS FAILED (python wrapper not installed)"; exit 1; }
grep -q "^PEAKSEARCH=[0-9]" rep_pod.sh || { echo "HARNESS FAILED (the search peak is not a measured number)"; exit 1; }
printf '%s\n' '#!/bin/bash' 'exec /opt/homebrew/bin/python3 "$@"' > pywrap; chmod +x pywrap
cp $SRC/podctl.py .
# code repository: one listed file; the manifest names this commit and the file's hash
mkdir -p g && (cd g && git init -q && mkdir -p docs/revision/followup3 && echo "plan" > docs/revision/followup3/replication-plan.md \
  && cp ../rep_pod.sh docs/revision/followup3/rep_pod.sh && git add -A && git -c commit.gpgsign=false -c user.email=x@x -c user.name=x commit -q -m x && git -c tag.gpgsign=false tag protocol-v2 \
  && COPYFILE_DISABLE=1 tar --uid 0 --gid 0 -czf ../c.tgz .)
C=$(git -C g rev-parse HEAD); export HC=$C
export WT REALUV=$(command -v uv) REALCACHE=$(uv cache dir 2>/dev/null)
# bundles: b1 (pod 1), b2 (pod 2: pod 1's verified output); variants that each guard must refuse
python3 - "$C" <<'EOF'
import hashlib, json, os, sys
c = sys.argv[1]; sha = lambda b: hashlib.sha256(b).hexdigest()
LH = sha(open("rep_pod.sh", "rb").read())        # the launcher under test, as the manifest lists it
def man(commit, h=None, lh=None):
    return {"commit": commit, "files": {"docs/revision/followup3/replication-plan.md": h or sha(b"plan\n"),
                                        "docs/revision/followup3/rep_pod.sh": lh or LH}, "note": "x"}
def draw(root, m):
    os.makedirs(f"{root}/draw", exist_ok=True)
    json.dump(m, open(f"{root}/draw/manifest.json", "w")); open(f"{root}/draw/manifest.json.ots", "wb").write(b"ots")
    json.dump({"hash": "ab"}, open(f"{root}/draw/draw.json", "w"))
def rep(root, system="Linux", tamper=False, extra=False, wrongdraw=False, launch="p1", machine="x86_64"):
    r = f"{root}/rep"; os.makedirs(f"{r}/menu/freeze", exist_ok=True)
    files = {"instances.json": b"{}", "salt.hex": b"00", "cfgs.json": b'{"fresh0": {}}', "menu/freeze/fresh0.json": b"{}"}
    bind = {"manifest_sha256": sha(open(f"{root}/draw/manifest.json", "rb").read()),
            "draw_sha256": "0" * 64 if wrongdraw else sha(open(f"{root}/draw/draw.json", "rb").read())}
    files["binding.json"] = json.dumps(bind).encode(); files["launch.json"] = json.dumps({"launch": launch}).encode()
    files["calibration.json"] = json.dumps({"cfgs_sha256": sha(files["cfgs.json"]), "system": system, "machine": machine}).encode()
    for k, v in files.items():
        open(f"{r}/{k}", "wb").write(v)
    json.dump({"records": {k: sha(v) for k, v in files.items()}}, open(f"{r}/inventory.json", "w"))
    if tamper: open(f"{r}/menu/freeze/fresh0.json", "w").write('{"x": 1}')
    if extra: open(f"{r}/stray.json", "w").write("{}")
for root, m in (("b1", man(c)), ("b1nocommit", man("0" * 40)), ("b1badhash", man(c, "0" * 64)), ("b1otherlauncher", man(c, lh="0" * 64))):
    draw(root, m)
os.makedirs("b1noproof/draw", exist_ok=True); json.dump(man(c), open("b1noproof/draw/manifest.json", "w")); json.dump({}, open("b1noproof/draw/draw.json", "w"))
for root, kw in (("b2", {}), ("b2mac", {"system": "Darwin"}), ("b2tamper", {"tamper": True}), ("b2extra", {"extra": True}),
                 ("b2wrongdraw", {"wrongdraw": True}), ("b2otherlaunch", {"launch": "p9"}), ("b2arm", {"machine": "aarch64"})):
    draw(root, man(c)); rep(root, **kw)
EOF
for b in b1 b1nocommit b1badhash b1noproof b1otherlauncher b2 b2mac b2tamper b2extra b2wrongdraw b2otherlaunch b2arm; do (cd $b && tar czf ../$b.tgz .); done
# prepared remote output with a complete inventory, for the RUN OK scenarios
python3 - <<'EOF'
import hashlib, json, os
d = "remote/followup3-rep"
os.makedirs(d + "/sub", exist_ok=True); open(f"{d}/r.json", "w").write('{"x": 1}'); open(f"{d}/sub/s.json", "w").write('{"y": 2}')
recs = {k: hashlib.sha256(open(f"{d}/{k}", "rb").read()).hexdigest() for k in ("r.json", "sub/s.json")}
json.dump({"records": recs}, open(f"{d}/inventory.json", "w"))
EOF
cat > runpod.py <<'EOF'
import fcntl, json, os, shutil, sys
H = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(H, "state.json")
L = open(S + ".lock", "w"); fcntl.flock(L, fcntl.LOCK_EX)    # held until exit: one transaction per call
st = json.load(open(S)); cmd, a = sys.argv[1], sys.argv[2:]; st["log"].append(" ".join([cmd] + a[:1])); rc = 0
for p in list(st.get("pending", {})):                       # delayed creations appear after a countdown of calls
    st["pending"][p][1] -= 1
    if st["pending"][p][1] <= 0: st["pods"][p] = st["pending"].pop(p)[0]
if cmd == "list":
    if st.get("fail_list", 0) > 0: st["fail_list"] -= 1; rc = 1; print("error")
    else: print(json.dumps([{"id": i, "name": n, "costPerHr": st["price"]} for i, n in st["pods"].items()]))
elif cmd == "balance":
    if st.get("bal_fail"): rc = 1; print("error")
    else: print(json.dumps({"balance": 100.0, "spendPerHr": 0}))
elif cmd == "delete":
    if st.get("stuck", {}).get(a[0], 0) > 0: st["stuck"][a[0]] -= 1
    else: st["pods"].pop(a[0], None)
    print("{}")
elif cmd == "ssh":
    c = a[1] if len(a) > 1 else ""
    down = st.get("down_first") and st.get("created") and a[0] == st["created"][0][0]   # the first pod never answers
    if not st["up"] or down: rc = 255; print("")
    elif "git rev-parse" in c:
        if st.get("mutate_ledger"):                     # the operator edits the ledger after the deadlines were computed
            led = json.load(open(os.path.join(H, "ledger.json"))); led["spent"].append({"op": "followup", "tag": "replication-late", "usd": 9.0})
            json.dump(led, open(os.path.join(H, "ledger.json"), "w"))
        print(f"git={os.environ.get('HC','')} env=unset bundle=3 memgb={st.get('memgb', 64)} py=x")
    elif "tail -c 240" in c: print("== remote started 11:48 == cthr start 11:48 == RUN OK 12:00" if st.get("runok") else st.get("remote_tail", "== remote started 11:48 == menu start 11:50"))
    else: print("up")
elif cmd == "push":
    if st.get("push_fail"): rc = 1; print("exit 1")
    else:
        b = os.path.basename(a[2])
        if b in ("r_remote.sh", "rep.attempts", "rep.ledger.json"): shutil.copy(a[1], os.path.join(H, "pushed_" + b))   # kept for the checks
        print("exit 0")
elif cmd == "pull":
    src, dst = a[1], a[2]
    if "followup3-rep" in src:
        if st.get("fail_pull"):
            rc = 1
        elif st.get("fail_pulls", 0) > 0:                   # the first N pulls fail before any file arrives
            st["fail_pulls"] -= 1; rc = 1
        else:
            shutil.copytree(os.path.join(H, "remote", "followup3-rep"), dst, dirs_exist_ok=True)
            if st.get("partial_pull"): rc = 1
            if st.get("corrupt_pulls", 0) > 0:
                st["corrupt_pulls"] -= 1; open(os.path.join(dst, "sub", "s.json"), "w").write("corrupt")
json.dump(st, open(S, "w")); sys.exit(rc)
EOF
cat > create_one.py <<'EOF'
import fcntl, json, os, signal, subprocess, sys
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
L = open(S + ".lock", "w"); fcntl.flock(L, fcntl.LOCK_EX)
st = json.load(open(S))
import time
pid = "pod%d" % (len(st["log"]) + 1); st["log"].append("create " + pid); st.setdefault("created", []).append([pid, time.time()])
if st.get("delay"): st.setdefault("pending", {})[pid] = [sys.argv[1], st["delay"]]
else: st["pods"][pid] = sys.argv[1]
if st.get("stuck_next"): st.setdefault("stuck", {})[pid] = 40; st["stuck_next"] = False
amb = bool(st.get("lose")); term = bool(st.get("term")); json.dump(st, open(S, "w")); L.close()
if term:   # a stop during creation (r15): TERM the launcher while this request is outstanding; it answers nothing
    p = os.getppid(); top = None
    while p > 1:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(p)], capture_output=True, text=True).stdout
        if "snap_rep_pod" in cmd: top = p
        p = int(subprocess.run(["ps", "-o", "ppid=", "-p", str(p)], capture_output=True, text=True).stdout.strip() or 1)
    if top: os.kill(top, signal.SIGTERM)
    sys.exit(1)
print(json.dumps({"id": "" if amb else pid, "ambiguous": amb, "vcpu": 16}))
EOF
# ledger: LEDGERV selects a variant; the reservation covers the watchdog bound HARD x 33 at the plan cap
ledger() { python3 - "$1" "${2:-0}" <<'EOF'
import json, sys
v, prior = sys.argv[1], float(sys.argv[2])
d = {"caps": {"followup": 72.0}, "reservations": [{"op": "followup", "tag": "replication-t", "cap": 42.9}],
     "spent": [{"op": "followup", "tag": "reset-pod", "usd": 1.65}, {"op": "followup", "tag": "convergence2-1", "usd": 3.40}]}
if prior:
    d["spent"].append({"op": "followup", "tag": "replication-0", "usd": prior})
if v == "pod1":
    d["spent"].append({"op": "followup", "tag": "replication-p1", "usd": 6.0})          # pod 1's recorded spend
if v == "pod1open":
    d["reservations"].append({"op": "followup", "tag": "replication-p1", "cap": 42.9})  # pod 1 ran, its spend not recorded
if v == "nores":
    d["reservations"] = [{"op": "followup", "tag": "replication-t", "cap": 3.0}]        # the stop cap only: below the bound
if v == "wrongop":
    d["reservations"] = [{"op": "development", "tag": "replication-t", "cap": 42.9}]
if v == "reused":
    d["spent"].append({"op": "followup", "tag": "replication-t", "usd": 0.5})
if v == "badrow":
    d["spent"].append({"op": "followup", "tag": "replication-x", "usd": float("nan")})
open("ledger.json", "w").write(json.dumps(d))
EOF
}
fail=0; ran=0; TOTAL=47
run() { # name state cap creates rc [end-pattern] [watchdog-log-substring] [launcher-output-substring]; env RUNV (1), BUN
  [ -n "${ONLY:-}" ] && ! echo "$1" | grep -q "$ONLY" && return 0   # smoke runs only; a full run sets no ONLY
  r=${RUNV:-1}; T=${TAGV:-t}; N=ts-rep; LG=logs_rep${r}_$T; B=${BUN:-}; [ -n "$B" ] || { [ "$r" = 2 ] && B=b2.tgz || B=b1.tgz; }
  ran=$((ran+1)); echo "== $1"; echo "$2" > state.json; mkdir -p $LG junk; : > $LG/watchdog.log; : > $N.wdpid
  for f in $N.bal0 $N.spent $N.wdend; do [ -e $f ] && mv -- $f junk/$f.$ran; done   # isolation: one launch per scenario
  [ -n "${PRELOCK:-}" ] && mkdir $N.launchlock
  [ -n "${PREBAL:-}" ] && echo "100.0 0.0" > $N.bal0
  ledger "${LEDGERV:-ok}" "${PRIORV:-0}"
  if [ -n "${PRIORENV:-}" ]; then
    POD1TAG=${POD1V-p1} PRIOR=$PRIORENV PUBH=${PUBHV:-974999} EXPECT=$C MAXCPH=0.70 HARD=${HARDX:-1.3} LEDGER=$H/ledger.json DRYRUN=${DRY:-} perl -e 'alarm 1500; exec @ARGV' bash rep_pod.sh $r c.tgz $B $T $3 out > run.out 2>&1; lrc=$?
  else
    POD1TAG=${POD1V-p1} PUBH=${PUBHV:-974999} EXPECT=$C MAXCPH=0.70 HARD=${HARDX:-1.3} LEDGER=$H/ledger.json DRYRUN=${DRY:-} perl -e 'alarm 1500; exec @ARGV' bash rep_pod.sh $r c.tgz $B $T $3 out > run.out 2>&1; lrc=$?
  fi
  out=$(grep -v "^tarball\|code guard\|bundle guard\|^commitment:\|^ledger:" run.out); echo "$out" | tail -3
  wd=$(cat $N.wdpid 2>/dev/null); alive=""
  for i in $(seq 1 ${WAITW:-800}); do [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null || break; sleep 3; done
  if [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null; then alive=1; kill "$wd"; sleep 1; echo "watchdog $wd still running; stopped"; fi
  read left creates <<< "$(python3 -c "import json;s=json.load(open('state.json'));print(len(s['pods'])+len(s.get('pending',{})), sum(1 for l in s['log'] if l.startswith('create')))")"
  echo "pods left: $left, creation requests: $creates (expected $4), exit $lrc (expected $5)"; tail -1 $LG/watchdog.log
  [ "$left" = 0 ] && [ "$creates" = "$4" ] && [ "$lrc" = "$5" ] || { echo "SCENARIO FAILED"; fail=1; }
  [ -z "${6:-}" ] || echo "$out" | grep -Eq "^[0-9]{2}:[0-9]{2} end: ($6)\$" || { echo "SCENARIO FAILED (end line is not: $6)"; fail=1; }
  [ -z "${7:-}" ] || grep -q "$7" $LG/watchdog.log || { echo "SCENARIO FAILED (watchdog log lacks: $7)"; fail=1; }
  [ -z "${8:-}" ] || grep -Eq "$8" run.out || { echo "SCENARIO FAILED (launcher output lacks: $8)"; fail=1; }
  [ -z "${NOTOUT:-}" ] || ! { echo "$out"; cat $LG/watchdog.log; } | grep -q "$NOTOUT" || { echo "SCENARIO FAILED (output contains: $NOTOUT)"; fail=1; }
  if [ -n "${WD_ALIVE:-}" ]; then [ -n "$alive" ] || { echo "SCENARIO FAILED (the watchdog should have stayed, fail-closed)"; fail=1; }
  elif [ -n "$alive" ]; then echo "SCENARIO FAILED (the watchdog did not end by itself)"; fail=1; fi
  if [ -z "${PRELOCK:-}" ] && [ -z "$alive" ] && [ -d $N.launchlock ]; then echo "SCENARIO FAILED (launch lock not released)"; fail=1; fi
  [ -z "${PREBAL:-}" ] || [ -e $N.bal0 ] || { echo "SCENARIO FAILED (the previous spend baseline was not kept)"; fail=1; }
  python3 podctl.py unlock $N >/dev/null 2>&1; true; }
E='{"pods":{},"price":0.56,"up":true,"log":[]}'
# --- refusals before any marker
RUNV=3 run "an unknown pod number is refused" "$E" 3 0 1 "" "" "^refused: the pod must be 1 or 2"
PRIORENV=1 run "PRIOR from the environment is refused (it comes from the ledger)" "$E" 3 0 1 "" "" "^refused: PRIOR is not an input here"
run "a cap above the plan's is refused" "$E" 33.01 0 1 "" "" "^refused: the cap must be positive and at most the plan's 33.00 USD"
PUBHV=soon run "a publication height that is neither a number nor none is refused" "$E" 3 0 1 "" "" "^refused: PUBH must be a block height or none"
LEDGERV=nores run "a reservation below the watchdog bound is refused" "$E" 3 0 1 "" "" "^refused: no single followup reservation replication-t covers the watchdog bound 3.9000 USD"
LEDGERV=wrongop run "a reservation in another category is refused" "$E" 3 0 1 "" "" "^refused: no single followup reservation replication-t covers"
LEDGERV=reused run "a launch tag that already has a spend record is refused" "$E" 3 0 1 "" "" "^refused: replication-t already has a spend record"
LEDGERV=badrow run "a malformed ledger row is refused" "$E" 3 0 1 "" "" "^refused: a malformed spend row in the ledger"
BUN=b1noproof.tgz run "pod 1: a bundle without the manifest proof is refused" "$E" 3 0 1 "" "" "^bundle refused"
BUN=b1nocommit.tgz run "pod 1: a manifest whose commit is not in the code history is refused" "$E" 3 0 1 "" "" "is not an ancestor of HEAD"
BUN=b1badhash.tgz run "pod 1: a listed file whose hash differs from the manifest is refused" "$E" 3 0 1 "" "" "^commitment: 2 listed files, 1 differ"
BUN=b1otherlauncher.tgz run "a launcher whose bytes differ from the manifest's rep_pod.sh is refused" "$E" 3 0 1 "" "" "this launcher differs from the manifest"
DRY=1 run "pod 1 dry run: every guard passes, no pod" "$E" 3 0 0 "" "" "^dry run: guards passed; no pod created"
PUBHV=none DRY=1 run "pod 1 dry run without a publication height (nonconfirmatory)" "$E" 3 0 0 "" "" "^dry run: guards passed; no pod created"
RUNV=2 run "pod 2 is refused while pod 1's spend is not recorded" "$E" 3 0 1 "" "" "^refused: pod 1's spend \(replication-p1\) is not recorded"
POD1V= RUNV=2 run "pod 2 is refused without pod 1's launch tag" "$E" 3 0 1 "" "" "^refused: pod 2 needs POD1TAG"
POD1V=t LEDGERV=pod1 RUNV=2 run "pod 2 is refused when its launch tag equals pod 1's" "$E" 33 0 1 "" "" "^refused: pod 2's launch tag must differ"
POD1V=p9 LEDGERV=pod1 RUNV=2 BUN=b2otherlaunch.tgz run "pod 2 is refused when pod 1's named spend row is absent" "$E" 33 0 1 "" "" "^refused: pod 1's spend \(replication-p9\) is not recorded"
LEDGERV=pod1open RUNV=2 run "pod 2 is refused while pod 1's reservation is open" "$E" 3 0 1 "" "" "^refused: (pod 1's spend|open reservations)"
LEDGERV=pod1 RUNV=2 BUN=b2mac.tgz run "pod 2: a calibration not made on Linux is refused" "$E" 33 0 1 "" "" "was not made on Linux"
LEDGERV=pod1 RUNV=2 BUN=b2arm.tgz run "pod 2: a calibration not made on x86 is refused" "$E" 33 0 1 "" "" "was not made on Linux x86 \\('Linux' 'aarch64'\\)"
LEDGERV=pod1 RUNV=2 BUN=b2tamper.tgz run "pod 2: pod 1 output whose inventory does not verify is refused" "$E" 33 0 1 "" "" "rep/ inventory: 7 records, 1 bad, 0 not inventoried"
LEDGERV=pod1 RUNV=2 BUN=b2extra.tgz run "pod 2: a file outside pod 1's inventory is refused" "$E" 33 0 1 "" "" "rep/ inventory: 7 records, 0 bad, 1 not inventoried"
LEDGERV=pod1 RUNV=2 BUN=b2wrongdraw.tgz run "pod 2: pod 1 output bound to another draw is refused" "$E" 33 0 1 "" "" "rep/binding.json does not match this bundle"
LEDGERV=pod1 RUNV=2 BUN=b2otherlaunch.tgz run "pod 2: pod 1 output of another launch is refused" "$E" 33 0 1 "" "" "rep/launch.json names launch 'p9', not POD1TAG 'p1'"
LEDGERV=pod1 RUNV=2 DRY=1 run "pod 2 dry run: pod 1 recorded, its output verified, PRIOR 6.0" "$E" 33 0 0 "" "" "^ledger: PRIOR 6.0 USD recorded for replication"
# --- the shared pre-pod path (from the churn and follow-up harnesses), with pod 1
NOTOUT="pull or verification failed" run "price above the ceiling: deleted at once, no retrieval" '{"pods":{},"price":0.9,"up":true,"log":[]}' 3 1 1 "PRICE 0.9 NOT IN \(0, 0.70\]"
run "an ambiguous answer ends creation: one request, no retry" '{"pods":{},"price":0.56,"up":true,"log":[],"lose":true}' 3 1 1 "AMBIGUOUS CREATION ANSWER \(no retry\)" "for 1800s" "UNRESOLVED"
run "a stop during creation leaves the request pending; the late pod is deleted (r15)" '{"pods":{},"price":0.56,"up":true,"log":[],"term":true,"delay":20}' 3 1 1 "NOT STARTED" "for 1800s" "outstanding or ambiguous"
HARDX=1.0 run "deletion keeps failing: the watchdog deletes after the deadline" '{"pods":{},"price":0.56,"up":false,"log":[],"stuck_next":true}' 0.004 1 1 "UNREACHABLE POD NOT DELETED|CREATION BLOCKED \(hard deadline\)|SOFT DEADLINE BEFORE START|NO POD" "WATCHDOG: deleting"
WD_ALIVE=1 WAITW=20 run "listing always fails: no creation; the watchdog stays (fail-closed)" '{"pods":{},"price":0.56,"up":true,"log":[],"fail_list":1000000}' 3 0 1 "RECONCILE FAILED BEFORE REQUEST 1"
PRELOCK=1 run "a held launch lock refuses the launch" "$E" 3 0 1 "" "" "^LOCKED: ts-rep.launchlock exists"
PRELOCK=1 LEDGERV=pod1 RUNV=2 run "pod 2 shares pod 1's launch lock" "$E" 33 0 1 "" "" "^LOCKED: ts-rep.launchlock exists"
PREBAL=1 run "an unrecorded previous spend refuses the launch and keeps its baseline" "$E" 3 0 1 "" "" "^refused: the previous launch's spend is not recorded"
run "a pod below the minimum memory is refused at preparation" '{"pods":{},"price":0.56,"up":true,"log":[],"memgb":16}' 3 1 1 "PREP FAILED \(memory 16 GB < 28 GB\)"
run "pod 1: RUN OK with one corrupt pull, retried until verified; a ledger edit after the deadlines does not reach the pod" '{"pods":{},"price":0.56,"up":true,"log":[],"runok":true,"corrupt_pulls":1,"mutate_ledger":true}' 3 1 0 "RUN OK" "" "verify followup3-rep: 2 records, 0 bad, 0 not inventoried"
cp pushed_r_remote.sh pushed_1.sh
python3 - <<'PYS' || { echo "SCENARIO FAILED (ledger snapshot)"; fail=1; }
import json
now, pushed = json.load(open("ledger.json")), json.load(open("pushed_rep.ledger.json"))
assert any(r["tag"] == "replication-late" for r in now["spent"]) and not any(r["tag"] == "replication-late" for r in pushed["spent"])
print("ledger snapshot ok: the pushed copy is the one validated before the deadlines")
PYS
run "pod 1: records pulled after a failure are verified too" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== remote started 11:48 == menu start 12:00 == RUN FAILED at menu 13:00"}' 3 1 1 "== RUN FAILED at menu 13:00" "" "verify followup3-rep: 2 records, 0 bad, 0 not inventoried"
run "pod 1: a failure-state pull that fails is retried before deletion" '{"pods":{},"price":0.56,"up":true,"log":[],"fail_pulls":1,"remote_tail":"== remote started 11:48 == menu start 12:00 == RUN FAILED at menu 13:00"}' 3 1 1 "== RUN FAILED at menu 13:00" "" "verify followup3-rep: 2 records, 0 bad, 0 not inventoried"
grep -q "pull or verification failed (try 1)" run.out || { echo "SCENARIO FAILED (no retry after a failed pull on a failure state)"; fail=1; }
run "pod 1: a pull that reports failure after the files arrived is still verified" '{"pods":{},"price":0.56,"up":true,"log":[],"partial_pull":true,"remote_tail":"== remote started 11:48 == menu start 12:00 == RUN FAILED at menu 13:00"}' 3 1 1 "== RUN FAILED at menu 13:00" "" "verify followup3-rep: 2 records, 0 bad, 0 not inventoried"
LEDGERV=pod1 RUNV=2 run "pod 2: RUN OK, records verified" '{"pods":{},"price":0.56,"up":true,"log":[],"runok":true}' 33 1 0 "RUN OK" "" "verify followup3-rep: 2 records, 0 bad, 0 not inventoried"
cp pushed_r_remote.sh pushed_2.sh
LEDGERV=pod1 RUNV=2 run "pod 2: the end state is the last line of the polled tail (a gate failure)" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== remote started 11:48 == gate0 start 12:00 == GATE FAILED at gate0 (churn path not bit-identical at p = 0) 13:00"}' 33 1 1 "== GATE FAILED at gate0 \(churn path not bit-identical at p = 0\) 13:00"
# Accounting: the ledger records 1.2 USD for the run tag (PRIOR), and a first pod never answers (deleted after 240 s). The
# deadlines leave CAP - PRIOR and HARD x CAP - PRIOR; the pushed attempts file has the deleted attempt and one open start,
# the live pod's request time (= --started-at and --started); the driver's --prior-usd adds the closed attempt at 0.70.
PRIORV=1.2 run "pod 1: ledger PRIOR and a deleted attempt count against the deadlines and both admissions" '{"pods":{},"price":0.56,"up":true,"log":[],"down_first":true,"remote_tail":"== STOPPED BEFORE instances (cap, admission) 12:00"}' 3 2 1 "== STOPPED BEFORE instances \(cap, admission\) 12:00"
python3 - "$H" <<'PYC' || { echo "SCENARIO FAILED (accounting)"; fail=1; }
import json, re, sys
H = sys.argv[1]; out = open(f"{H}/run.out").read(); sc = open(f"{H}/pushed_r_remote.sh").read()
st = json.load(open(f"{H}/state.json")); att = [l.split() for l in open(f"{H}/pushed_rep.attempts")]
m = re.search(r"soft stop in (\d+)s, hard stop in (\d+)s", out); soft, hard = int(m[1]), int(m[2])
assert int(3600 * 1.8 / 0.70) - 900 < soft <= int(3600 * 1.8 / 0.70) and hard <= int(3600 * (3.9 - 1.2) / 0.70), (soft, hard)
starts = {f[0]: int(f[1]) for f in att if f[2] == "start"}; dels = {f[0]: int(f[1]) for f in att if f[2] == "deleted"}
(p1, c1), (p2, c2) = st["created"][0], st["created"][1]
assert set(starts) == {p1, p2} and set(dels) == {p1} and dels[p1] - starts[p1] >= 240, (starts, dels)
paid = re.search(r'PAID="([^"]*)"', sc)[1]; rp = re.search(r'RP="([^"]*)"', sc)[1]
started = int(re.search(r"--started-at (\d+)", paid)[1]); assert started == starts[p2] and started <= c2
for f in ("--cap-usd 3 ", "--usd-per-hour 0.70 ", "--run-tag replication ", "--attempts $R/rep.attempts", "--ledger $R/rep.ledger.json", "--stop-file $R/STOP"):
    assert f in paid + " ", f
assert int(re.search(r"--started (\d+)", rp)[1]) == started and "--stop-usd 3 " in rp and "--usd-per-hour 0.70 " in rp and "--stop-file $R/STOP" in rp
px = float(re.search(r"--prior-usd ([0-9.]+)", rp)[1]); closed = (dels[p1] - starts[p1]) / 3600 * 0.70
assert abs(px - (1.2 + closed)) < 1e-4 and px > 1.2 + 240 / 3600 * 0.70 - 1e-6, (px, closed)
for x in (paid, rp):
    sd = int(re.search(r"--soft-deadline (\d+)", x)[1]); assert abs((sd - started) - soft) < 60, (sd, started, soft)
assert "ledger: PRIOR 1.2 USD recorded for replication" in out
print(f"accounting ok: soft {soft}s, hard {hard}s, PRIOR 1.2, driver prior {px:.4f} with the closed attempt")
PYC
cp pushed_r_remote.sh pushed_acct.sh; cp pushed_rep.attempts acct.attempts; cp pushed_rep.ledger.json acct.ledger.json
# The generated remote scripts, executed under a scratch root with a stub `uv` (logs each call; acts as $STUB says).
mkdir -p stubbin junk
cat > stubbin/uv <<'EOF'
#!/bin/bash
# stub for `uv run --frozen python <script> ...`. STUB words: admit@<hours>=refuse|crash, <stage>=crash|cap|gatefail|mm|lost|lostonce|lostnoest|lostthenerr|cellerr
# (stage: instances, calibrate, menu, cthr, inventory, rates-p0, rates-churn, gate0, continue)
echo "$*" >> "$REMOTE_ROOT/calls.log"
if [ -n "${REALADMIT:-}" ] && [ "${4##*/}" = guards.py ]; then         # the real admission, not a stub exit code
  cd "$WT" && UV_CACHE_DIR="$REALCACHE" exec "$REALUV" run --frozen python docs/revision/followup2/guards.py "${@:5}"
fi
s=$4; hours=""; stage=""; rates=""; prev=""
for i in "$@"; do [ "$prev" = "--hours" ] && hours=$i; [ "$prev" = "--stage" ] && stage=$i; [ "$prev" = "--rates" ] && rates=$i; prev=$i; done
case "$s" in *guards.py) what="admit@$hours" ;; *) what=$stage; [ -n "$rates" ] && what="$stage-$rates" ;; esac
act=""; for w in $STUB; do [ "${w%%=*}" = "$what" ] && act=${w#*=}; done
O=results/v2/followup3-rep
case "$what:$act" in
  admit*:refuse) echo '{"stopped_before": "next step"}'; exit 3 ;;
  admit*:crash) echo "follow-up refused: no launcher attempts file"; exit 1 ;;
  *:crash) echo "Traceback (most recent call last): ValueError"; exit 1 ;;
  *:cap) echo "SystemExit: churn arm stopped between stages: 2.00 USD billed + 1.50 USD for the next stage would pass the 3.00 USD cap"; exit 1 ;;
  *:gatefail) echo "replication refused: the churn-zero gate failed"; exit 1 ;;
  *:mm) exit 4 ;;
  *:lost*) mkdir -p $O/continuation
    if [ "$act" = lostnoest ]; then echo '{"lost": ["x"]}'; else echo '{"lost": ["x"], "restart_hours": {"1": 9.9, "3": 2.75, "5": 1.5}}'; fi > $O/continuation/lost_cells.json
    [ "$act" = lostonce ] && { [ -e "$REMOTE_ROOT/lost1" ] && exit 0; touch "$REMOTE_ROOT/lost1"; }
    [ "$act" = lostthenerr ] && { [ -e "$REMOTE_ROOT/lost1" ] && exit 6; touch "$REMOTE_ROOT/lost1"; }; exit 5 ;;
  *:cellerr) exit 6 ;;
  *:c3) exit 3 ;;
esac
exit 0
EOF
chmod +x stubbin/uv
rcheck() { # SCRIPT STUB expected-last-line [STOPFILE]; env REALADMIT: the real guards.py with the accounting launch's pushed files
  rr=$(mktemp -d); mkdir -p $rr/touchstone/results/logs $rr/bundle/rep $rr/.local/bin
  [ "${1##*/}" = pushed_2.sh ] || mkdir -p $rr/touchstone/results/v2/followup3-rep   # made by the instances stage on the pod
  cp stubbin/uv $rr/.local/bin/uv; [ -n "${4:-}" ] && touch $rr/STOP
  [ -n "${REALADMIT:-}" ] && { cp acct.attempts $rr/rep.attempts; cp acct.ledger.json $rr/rep.ledger.json; }
  last=$(REMOTE_ROOT=$rr HOME=$rr STUB="$2" bash $1 2>&1 | tail -n 1)
  echo "$last" | grep -Eq "^$3 [0-9]{2}:[0-9]{2}\$" || { echo "SCENARIO FAILED (remote $1, STUB='$2': last line '$last', expected '$3')"; fail=1; }
  RCALLS=$(cat $rr/calls.log 2>/dev/null); RADMIT=$(cat $rr/touchstone/results/logs/rep_admit.log 2>/dev/null); mv -- $rr junk/rr.$RANDOM; }
ran=$((ran+1)); echo "== pod 1: the generated remote script with a stub driver"
rcheck pushed_1.sh "admit@0.05=refuse" "== STOPPED BEFORE instances \(cap, admission\)"
rcheck pushed_1.sh "admit@0.05=crash" "== RUN FAILED at admission before instances"
rcheck pushed_1.sh "instances=crash" "== RUN FAILED at instances"
rcheck pushed_1.sh "calibrate=crash" "== RUN FAILED at calibrate"
rcheck pushed_1.sh "admit@7.60=refuse" "== STOPPED BEFORE menu \(cap, admission\)"
rcheck pushed_1.sh "menu=crash" "== RUN FAILED at menu"
echo "$RCALLS" | tail -n 1 | grep -q -- "--stage inventory" || { echo "SCENARIO FAILED (pod 1: a failure exit did not write the inventory first)"; fail=1; }
rcheck pushed_1.sh "cthr=crash" "== RUN FAILED at cthr"
rcheck pushed_1.sh "inventory=crash" "== RUN FAILED at inventory"
rcheck pushed_1.sh "" "== STOPPED BEFORE instances \(cap\)" stop
echo "$RCALLS" | tail -n 1 | grep -q -- "--stage inventory" || { echo "SCENARIO FAILED (pod 1: a stop exit did not write the inventory first)"; fail=1; }
rcheck pushed_1.sh "" "== RUN OK"
python3 - "$RCALLS" <<'PYR' || { echo "SCENARIO FAILED (pod 1 remote calls)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]; j = [" ".join(x) for x in c]
g, d = "docs/revision/followup2/guards.py", "docs/revision/followup3/rep_v2.py"
assert [x[3] for x in c] == [g, d, g, d, g, d, g, d, d], [x[3] for x in c]
assert all(x[:3] == ["run", "--frozen", "python"] for x in c)
assert [x.split("--stage ")[1].split()[0] for x in j if "--stage" in x] == ["instances", "calibrate", "menu", "cthr", "inventory"]
assert ["--hours 0.05" in j[0], "--hours 0.25" in j[2], "--hours 7.60" in j[4], "--hours 1.95" in j[6]] == [True] * 4
for k in (1, 3, 5, 7, 8):
    assert "--out results/v2/followup3-rep" in j[k] and "/bundle/draw/manifest.json " in j[k] + " " and "--draw " in j[k] and "/bundle/draw/draw.json" in j[k], (k, j[k])
assert "/bundle/draw/draw.json" in j[1] and "/bundle/draw/manifest.json.ots" in j[1] and "--published-height 974999" in j[1]
for k in (5, 7):
    for f in ("--workers-search 16 ", "--peak-search ", "--started ", "--usd-per-hour 0.70 ", "--stop-usd 3 ", "--prior-usd ", "/STOP ", "--soft-deadline "):
        assert f in j[k] + " ", (k, f)
print("remote ok (pod 1): 10 end states; admit before each paid stage; instances, calibrate, menu, cthr, inventory")
PYR
ran=$((ran+1)); echo "== pod 2: the generated remote script with a stub driver"
rcheck pushed_2.sh "admit@1.68=refuse" "== STOPPED BEFORE rates p0 \(cap, admission\)"
rcheck pushed_2.sh "rates-p0=cap" "== STOPPED BEFORE a rates p0 stage \(cap, driver admission\)"
rcheck pushed_2.sh "rates-p0=crash" "== RUN FAILED at rates p0"
rcheck pushed_2.sh "gate0=gatefail" "== GATE FAILED at gate0 \(churn path not bit-identical at p = 0\)"
rcheck pushed_2.sh "gate0=cap" "== STOPPED BEFORE a gate0 stage \(cap, driver admission\)"
rcheck pushed_2.sh "gate0=crash" "== RUN FAILED at gate0"
rcheck pushed_2.sh "admit@9.05=refuse" "== STOPPED BEFORE rates churn \(cap, admission\)"
rcheck pushed_2.sh "rates-churn=cap" "== STOPPED BEFORE a rates churn stage \(cap, driver admission\)"
rcheck pushed_2.sh "rates-churn=crash" "== RUN FAILED at rates churn"
echo "$RCALLS" | tail -n 1 | grep -q -- "--stage inventory" || { echo "SCENARIO FAILED (pod 2: a failure exit did not write the inventory first)"; fail=1; }
rcheck pushed_2.sh "admit@0.51=refuse" "== STOPPED BEFORE continue \(cap, admission\)"
rcheck pushed_2.sh "continue=mm" "== GATE FAILED at continue \(round 1 differs from this run's doubling record\)"
rcheck pushed_2.sh "continue=cellerr" "== RUN FAILED at continue \(a cell error; see continuation records\)"
rcheck pushed_2.sh "continue=crash" "== RUN FAILED at continue"
rcheck pushed_2.sh "continue=c3" "== STOPPED BEFORE a continuation round \(cap, driver admission\)"
rcheck pushed_2.sh "continue=lost" "== RUN FAILED at continue \(a worker lost twice; saved cells kept\)"
rcheck pushed_2.sh "continue=lostnoest" "== RUN FAILED at continue restart \(no restart estimate in lost_cells.json\)"
rcheck pushed_2.sh "continue=lostthenerr" "== RUN FAILED at continue \(a cell error; see continuation records\)"
rcheck pushed_2.sh "continue=lostonce admit@2.75=refuse" "== STOPPED BEFORE continue restart \(cap, admission\)"
rcheck pushed_2.sh "inventory=crash" "== RUN FAILED at inventory"
rcheck pushed_2.sh "" "== RUN OK"
python3 - "$RCALLS" <<'PYR' || { echo "SCENARIO FAILED (pod 2 remote calls)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]; j = [" ".join(x) for x in c]
g, d = "docs/revision/followup2/guards.py", "docs/revision/followup3/rep_v2.py"
assert [x[3] for x in c] == [g, d] * 4 + [d], [x[3] for x in c]
st = [x.split("--stage ")[1].split()[0] + ("-" + x.split("--rates ")[1].split()[0] if "--rates" in x else "") for x in j if "--stage" in x]
assert st == ["rates-p0", "gate0", "rates-churn", "continue", "inventory"], st
assert ["--hours 1.68" in j[0], "--hours 1.20" in j[2], "--hours 9.05" in j[4], "--hours 0.51" in j[6]] == [True] * 4
for k in (1, 3, 5):
    for f in ("--workers-search 16 ", "--peak-search 254115840 ", "--workers-eval 9 ", "--draw ", "--stop-usd 33 ", "--prior-usd 6.0 ", "--started "):
        assert f in j[k] + " ", (k, f)
assert "--workers-cont 5 " in j[7] + " " and "--peak-cont 3540000000" in j[7] and "--stop-file " in j[7]
print("remote ok (pod 2): 20 end states; p0, gate0, churn, continue, inventory with the expected flags")
PYR
ran=$((ran+1)); echo "== pod 2: a lost continuation worker restarts the stage once on 3 workers"
rcheck pushed_2.sh "continue=lostonce" "== RUN OK"
python3 - "$RCALLS" <<'PYL' || { echo "SCENARIO FAILED (pod 2 restart)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]; j = [" ".join(x) for x in c]
assert [x[3].split("/")[-1] for x in c] == ["guards.py", "rep_v2.py"] * 5 + ["rep_v2.py"], [x[3] for x in c]
assert "--hours 2.75" in j[8] and "--workers-cont 5 " in j[7] + " " and "--workers-cont 3 " in j[9] + " ", j
print("restart ok: admission with the driver's estimate for 3 workers, then the stage again on 3 workers")
PYL
# The real admission: the accounting launch's script, attempts file and ledger (PRIOR 1.2 of a 3 USD cap, plus the deleted
# attempt), with the real guards.py: instances (0.05 h) and calibration (0.25 h) are admitted, the menu (7.60 h at 0.70)
# would pass the cap and is refused, so the script stops before it.
ran=$((ran+1)); echo "== the real guards.py admission inside the generated remote script"
REALADMIT=1 rcheck pushed_acct.sh "" "== STOPPED BEFORE menu \(cap, admission\)"
python3 - "$RCALLS" "$RADMIT" <<'PYA' || { echo "SCENARIO FAILED (real admission)"; fail=1; }
import json, sys
c = [l.split() for l in sys.argv[1].splitlines()]
assert [x[3].split("/")[-1] for x in c] == ["guards.py", "rep_v2.py", "guards.py", "rep_v2.py", "guards.py", "rep_v2.py"], c
assert "--stage inventory" in " ".join(c[-1]), c[-1]                    # the stop writes the inventory first (review r1)
rep = [json.loads(l) for l in sys.argv[2].splitlines() if l.startswith("{")]
assert len(rep) == 3 and [r["log"][-1]["allowed"] for r in rep] == [True, True, False], rep
assert rep[2]["prior_usd"] > 1.2 and rep[2]["cap_usd"] == 3.0, rep[2]
print(f"real admission ok: instances and calibration admitted, menu refused (prior {rep[2]['prior_usd']:.4f} USD incl. the deleted attempt)")
PYA
ran=$((ran+1)); echo "== the embedded verifier"
sed -n "/^verify() { \$PY - \"\$1\" <<'PYV'\$/,/^PYV\$/p" rep_pod.sh | sed '1d;$d' > verify.py
python3 - <<'PYT' || { echo "SCENARIO FAILED (verifier)"; fail=1; }
import hashlib, json, os, subprocess
def mk(d, files, listed):
    os.makedirs(d, exist_ok=True)
    for k, v in files.items():
        os.makedirs(os.path.dirname(f"{d}/{k}") or d, exist_ok=True); open(f"{d}/{k}", "w").write(v)
    json.dump({"records": {k: hashlib.sha256(files[k].encode()).hexdigest() for k in listed}}, open(f"{d}/inventory.json", "w"))
v = lambda d: subprocess.run(["python3", "verify.py", d], capture_output=True, text=True).returncode
mk("vt/ok", {"a.json": "1", "s/b.json": "2", "x.lock": "l", "s/inventory.json": "{}"}, ["a.json", "s/b.json"]); assert v("vt/ok") == 0
mk("vt/miss", {"a.json": "1"}, ["a.json"]); json.dump({"records": {"a.json": hashlib.sha256(b"1").hexdigest(), "gone.json": "0" * 64}}, open("vt/miss/inventory.json", "w")); assert v("vt/miss") == 1
mk("vt/chg", {"a.json": "1"}, ["a.json"]); open("vt/chg/a.json", "w").write("2"); assert v("vt/chg") == 1
mk("vt/extra", {"a.json": "1", "run.json": "{}"}, ["a.json"]); assert v("vt/extra") == 1
mk("vt/empty", {}, []); assert v("vt/empty") == 1
print("verifier ok: complete passes (nested rate inventories are indexes, not records); missing, changed, uninventoried and empty fail")
PYT
cd /; mv -- $H ~/.Trash/harness_rep_$$
if [ $fail != 0 ]; then echo "HARNESS FAILED"; exit 1; elif [ $ran != $TOTAL ]; then echo "HARNESS PARTIAL ($ran of $TOTAL scenarios ran)"; exit 2; else echo "HARNESS OK ($ran of $TOTAL scenarios)"; fi
