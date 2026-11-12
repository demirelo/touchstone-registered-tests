#!/bin/bash
# Offline harness for churn_pod.sh (derived from test_reset_pod_harness.sh) with podctl.py and create_one.py (no real pods). A fake runpod.py keeps pods, pending
# (delayed) creations and stuck deletions in state.json; a fake create_one.py makes one request per call. Every fake
# holds an exclusive lock on state.json for its whole read-modify-write (r15). Each scenario asserts: the pods left (0),
# the exact number of creation requests, the launcher exit status, the end state (an anchored pattern), that the
# watchdog ended by itself (unless the scenario expects it to stay, fail-closed) and released the launch lock, and, where
# stated, a watchdog log line, a launcher output line, and a line that must not appear (NOTOUT).
set -u; H=$(mktemp -d); cd $H; SRC=/Users/oemer.demirel/Projects/touchstone/results/pods
sed "s#P=/Users/oemer.demirel/Projects/touchstone/results/pods#P=$H#; s#snapf=\"/Users/oemer.demirel/Projects/touchstone/results/pods/snap_#snapf=\"$H/snap_#" $SRC/churn_pod.sh > churn_pod.sh
cp $SRC/podctl.py .
mkdir -p g && (cd g && git init -q && git -c commit.gpgsign=false -c user.email=x@x -c user.name=x commit -q --allow-empty -m x && git -c tag.gpgsign=false tag protocol-v2 && COPYFILE_DISABLE=1 tar --uid 0 --gid 0 -czf ../c.tgz .)
C=$(git -C g rev-parse HEAD); echo x > b; tar czf b.tgz b; export HC=$C
# prepared remote outputs with inventories, for the RUN OK scenario
python3 - <<'EOF'
import hashlib, json, os
for d in ("remote/followup-churn/gate-p0", "remote/followup-churn/p0.01", "remote/followup-churn/p0.05"):
    os.makedirs(d, exist_ok=True); open(f"{d}/r.json", "w").write('{"x": 1}')
    json.dump({"records": {"r.json": hashlib.sha256(open(f"{d}/r.json", "rb").read()).hexdigest()}}, open(f"{d}/inventory.json", "w"))
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
    if not st["up"]: rc = 255; print("")
    elif "git rev-parse" in c: print(f"git={os.environ.get('HC','')} env=unset bundle=6 memgb=64 py=x")
    elif "tail -c 240" in c: print("== RUN OK" if st.get("runok") else st.get("remote_tail", "== stage search"))
    else: print("up")
elif cmd == "push":
    if st.get("push_fail"): rc = 1; print("exit 1")
    else: print("exit 0")
elif cmd == "pull":
    src, dst = a[1], a[2]
    for k in ("followup-churn",):
        if k in src:
            shutil.copytree(os.path.join(H, "remote", k), dst, dirs_exist_ok=True)
            if st.get("corrupt_pulls", 0) > 0:
                st["corrupt_pulls"] -= 1; open(os.path.join(dst, "p0.01", "r.json"), "w").write("corrupt")
json.dump(st, open(S, "w")); sys.exit(rc)
EOF
cat > create_one.py <<'EOF'
import fcntl, json, os, signal, subprocess, sys
S = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
L = open(S + ".lock", "w"); fcntl.flock(L, fcntl.LOCK_EX)
st = json.load(open(S))
pid = "pod%d" % (len(st["log"]) + 1); st["log"].append("create " + pid)
if st.get("delay"): st.setdefault("pending", {})[pid] = [sys.argv[1], st["delay"]]
else: st["pods"][pid] = sys.argv[1]
if st.get("stuck_next"): st.setdefault("stuck", {})[pid] = 40; st["stuck_next"] = False
amb = bool(st.get("lose")); term = bool(st.get("term")); json.dump(st, open(S, "w")); L.close()
if term:   # a stop during creation (r15): TERM the launcher while this request is outstanding; it answers nothing
    p = os.getppid(); top = None   # the topmost process running the launcher snapshot (subshells share its command line)
    while p > 1:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(p)], capture_output=True, text=True).stdout
        if "snap_churn_pod" in cmd: top = p
        p = int(subprocess.run(["ps", "-o", "ppid=", "-p", str(p)], capture_output=True, text=True).stdout.strip() or 1)
    if top: os.kill(top, signal.SIGTERM)
    sys.exit(1)
print(json.dumps({"id": "" if amb else pid, "ambiguous": amb, "vcpu": 16}))
EOF
fail=0; ran=0; TOTAL=16
run() { # name state cap creates rc [end-pattern] [watchdog-log-substring] [launcher-output-substring]
  [ -n "${ONLY:-}" ] && ! echo "$1" | grep -q "$ONLY" && return 0   # smoke runs only; a full run sets no ONLY
  ran=$((ran+1)); echo "== $1"; echo "$2" > state.json; mkdir -p logs_c_t junk; : > logs_c_t/watchdog.log; : > ts-c-t.wdpid
  for f in ts-c-t.bal0 ts-c-t.spent ts-c-t.wdend; do [ -e $f ] && mv -- $f junk/$f.$ran; done   # isolation: one launch per scenario
  [ -n "${PRELOCK:-}" ] && mkdir ts-c-t.launchlock
  [ -n "${PREBAL:-}" ] && echo "100.0 0.0" > ts-c-t.bal0
  [ -n "${EMPTYSPENT:-}" ] && : > ts-c-t.spent
  EXPECT=$C MAXCPH=0.70 HARD=${HARDX:-1.3} PRIOR=${PRIORV:-0} perl -e 'alarm 1500; exec @ARGV' bash churn_pod.sh c.tgz b.tgz t $3 out > run.out 2>&1; lrc=$?
  out=$(grep -v "^tarball\|code guard" run.out); echo "$out" | tail -3
  # wait for THIS scenario's watchdog by its PID (r11); the settle while a request is pending is 30 minutes
  wd=$(cat ts-c-t.wdpid 2>/dev/null); alive=""
  for i in $(seq 1 ${WAITW:-800}); do [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null || break; sleep 3; done
  if [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null; then alive=1; kill "$wd"; sleep 1; echo "watchdog $wd still running; stopped"; fi
  read left creates <<< "$(python3 -c "import json;s=json.load(open('state.json'));print(len(s['pods'])+len(s.get('pending',{})), sum(1 for l in s['log'] if l.startswith('create')))")"
  echo "pods left: $left, creation requests: $creates (expected $4), exit $lrc (expected $5)"; tail -1 logs_c_t/watchdog.log
  [ "$left" = 0 ] && [ "$creates" = "$4" ] && [ "$lrc" = "$5" ] || { echo "SCENARIO FAILED"; fail=1; }
  [ -z "${6:-}" ] || echo "$out" | grep -Eq "^[0-9]{2}:[0-9]{2} end: ($6)\$" || { echo "SCENARIO FAILED (end line is not: $6)"; fail=1; }
  [ -z "${7:-}" ] || grep -q "$7" logs_c_t/watchdog.log || { echo "SCENARIO FAILED (watchdog log lacks: $7)"; fail=1; }
  [ -z "${8:-}" ] || echo "$out" | grep -Eq "$8" || { echo "SCENARIO FAILED (launcher output lacks: $8)"; fail=1; }
  [ -z "${NOTOUT:-}" ] || ! { echo "$out"; cat logs_c_t/watchdog.log; } | grep -q "$NOTOUT" || { echo "SCENARIO FAILED (output contains: $NOTOUT)"; fail=1; }
  if [ -n "${WD_ALIVE:-}" ]; then [ -n "$alive" ] || { echo "SCENARIO FAILED (the watchdog should have stayed, fail-closed)"; fail=1; }
  elif [ -n "$alive" ]; then echo "SCENARIO FAILED (the watchdog did not end by itself)"; fail=1; fi
  if [ -z "${PRELOCK:-}" ] && [ -z "$alive" ] && [ -d ts-c-t.launchlock ]; then echo "SCENARIO FAILED (launch lock not released)"; fail=1; fi
  [ -z "${PREBAL:-}" ] || [ -e ts-c-t.bal0 ] || { echo "SCENARIO FAILED (the previous spend baseline was not kept)"; fail=1; }
  python3 podctl.py unlock ts-c-t >/dev/null 2>&1; true; }   # test isolation only (a held or stale lock)
NOTOUT="pull or verification failed" run "price above the ceiling: deleted at once, no retrieval" '{"pods":{},"price":0.9,"up":true,"log":[]}' 5 1 1 "PRICE 0.9 NOT IN \(0, 0.70\]"
NOTOUT="pull or verification failed" run "null price: deleted at once (r12)" '{"pods":{},"price":null,"up":true,"log":[]}' 5 1 1 "PRICE unknown NOT IN \(0, 0.70\]"
run "an ambiguous answer ends creation: one request, no retry" '{"pods":{},"price":0.56,"up":true,"log":[],"lose":true}' 5 1 1 "AMBIGUOUS CREATION ANSWER \(no retry\)" "for 1800s" "UNRESOLVED"
run "a pod created long after an ambiguous answer (beyond 300 s) is deleted by the watchdog" '{"pods":{},"price":0.56,"up":true,"log":[],"lose":true,"delay":20}' 5 1 1 "AMBIGUOUS CREATION ANSWER \(no retry\)" "WATCHDOG: deleting"
run "a stop during creation leaves the request pending; the late pod is deleted (r15)" '{"pods":{},"price":0.56,"up":true,"log":[],"term":true,"delay":20}' 5 1 1 "NOT STARTED" "for 1800s" "outstanding or ambiguous"
HARDX=1.0 run "unreachable pod at the deadline" '{"pods":{},"price":0.56,"up":false,"log":[]}' 0.004 1 1 "CREATION BLOCKED \(hard deadline\)|SOFT DEADLINE BEFORE START|NO POD"
HARDX=1.0 run "deletion keeps failing: the watchdog deletes after the deadline" '{"pods":{},"price":0.56,"up":false,"log":[],"stuck_next":true}' 0.004 1 1 "UNREACHABLE POD NOT DELETED|CREATION BLOCKED \(hard deadline\)|SOFT DEADLINE BEFORE START|NO POD" "WATCHDOG: deleting"
WD_ALIVE=1 WAITW=20 run "listing always fails: no creation; the watchdog stays (fail-closed)" '{"pods":{},"price":0.56,"up":true,"log":[],"fail_list":1000000}' 5 0 1 "RECONCILE FAILED BEFORE REQUEST 1"
PRELOCK=1 run "a held launch lock refuses the launch (r15)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 5 0 1 "" "" "^LOCKED: ts-c-t.launchlock exists"
PREBAL=1 run "an unrecorded previous spend refuses the launch and keeps its baseline (r16)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 5 0 1 "" "" "^refused: the previous launch's spend is not recorded"
PREBAL=1 EMPTYSPENT=1 run "an empty spend record does not count as recorded (r17)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 5 0 1 "" "" "^refused: the previous launch's spend is not recorded"
run "unknown balance: no creation, lock released (r16)" '{"pods":{},"price":0.56,"up":true,"log":[],"bal_fail":true}' 5 0 1 "" "" "^refused: account balance unknown$"
NOTOUT="pull or verification failed" run "upload failure stops the run before it starts (r15)" '{"pods":{},"price":0.56,"up":true,"log":[],"push_fail":true}' 5 1 1 "UPLOAD FAILED \(code\)"
run "RUN OK with one corrupt pull: retried until verified" '{"pods":{},"price":0.56,"up":true,"log":[],"runok":true,"corrupt_pulls":1}' 5 1 0 "RUN OK" "" "podctl.py spend ts-c-t"
run "the driver's cap admission stops the run between stages (churn)" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== STOPPED BEFORE search (cap, driver admission) 12:00"}' 5 1 1 "== STOPPED BEFORE search \(cap, driver admission\) 12:00"
PRIORV=-1 run "a negative PRIOR refuses the launch before any marker (churn)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 5 0 1 "" "" "^refused: PRIOR must be a non-negative number"
cd /; mv -- $H ~/.Trash/harness_$$
# a filtered (ONLY) run can never pass: the gate needs every scenario (r16)
if [ $fail != 0 ]; then echo "HARNESS FAILED"; exit 1; elif [ $ran != $TOTAL ]; then echo "HARNESS PARTIAL ($ran of $TOTAL scenarios ran)"; exit 2; else echo "HARNESS OK ($ran of $TOTAL scenarios)"; fi
