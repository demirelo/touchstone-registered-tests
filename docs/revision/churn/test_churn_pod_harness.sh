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
    down = st.get("down_first") and st.get("created") and a[0] == st["created"][0][0]   # the first pod never answers
    if not st["up"] or down: rc = 255; print("")
    elif "git rev-parse" in c: print(f"git={os.environ.get('HC','')} env=unset bundle=6 memgb=64 py=x")
    elif "tail -c 240" in c: print("== RUN OK" if st.get("runok") else st.get("remote_tail", "== stage search"))
    else: print("up")
elif cmd == "push":
    if st.get("push_fail"): rc = 1; print("exit 1")
    else:
        if a[2].endswith("r_remote.sh"): shutil.copy(a[1], os.path.join(H, "pushed_r_remote.sh"))   # kept for the remote checks
        print("exit 0")
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
import time
pid = "pod%d" % (len(st["log"]) + 1); st["log"].append("create " + pid); st.setdefault("created", []).append([pid, time.time()])
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
fail=0; ran=0; TOTAL=20
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
PRIORV=inf run "an infinite PRIOR refuses the launch before any marker (churn r1)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 5 0 1 "" "" "^refused: PRIOR must be a non-negative number"
run "a gate cap refusal is a stop, not a gate failure (churn r1)" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== STOPPED BEFORE gate (cap, driver admission) 12:00"}' 5 1 1 "== STOPPED BEFORE gate \(cap, driver admission\) 12:00"
# Accounting (churn r1): PRIOR 2 of a 5 USD cap, and a first pod that never answers (deleted after 240 s). The deadlines
# leave CAP - PRIOR and HARD x CAP - PRIOR; --prior-usd is PRIOR plus the deleted attempt from its request time at the
# ceiling, rounded up; --started is the live pod's request time, not later than its creation.
PRIORV=2 run "PRIOR and a deleted attempt count against the deadlines and the driver's admission (churn r1)" '{"pods":{},"price":0.56,"up":true,"log":[],"down_first":true,"remote_tail":"== STOPPED BEFORE search (cap, driver admission) 12:00"}' 5 2 1 "== STOPPED BEFORE search \(cap, driver admission\) 12:00"
python3 - "$H" <<'PYC' || { echo "SCENARIO FAILED (accounting)"; fail=1; }
import json, re, sys
H = sys.argv[1]; out = open(f"{H}/run.out").read(); sc = open(f"{H}/pushed_r_remote.sh").read()
st = json.load(open(f"{H}/state.json")); att = [l.split() for l in open(f"{H}/ts-c-t.attempts")]
m = re.search(r"soft stop in (\d+)s, hard stop in (\d+)s", out); soft, hard = int(m[1]), int(m[2])
assert soft <= int(3600 * 3 / 0.70) and hard <= int(3600 * (6.5 - 2) / 0.70), (soft, hard)
assert soft > int(3600 * 3 / 0.70) - 900, soft                     # less PRIOR, not less something larger
starts = {f[0]: int(f[1]) for f in att if f[2] == "start"}; dels = {f[0]: int(f[1]) for f in att if f[2] == "deleted"}
(p1, c1), (p2, c2) = st["created"][0], st["created"][1]
raw = 2 + (dels[p1] - starts[p1]) / 3600 * 0.70
prior = float(re.search(r"--prior-usd (\S+)", sc)[1]); started = int(re.search(r"--started (\d+)", sc)[1])
assert raw <= prior < raw + 0.0002, (prior, raw)
assert dels[p1] - starts[p1] >= 240 and starts[p1] <= c1, (starts, c1)
assert started == starts[p2] and started <= c2, (started, starts, c2)
assert re.search(r"--stop-usd 5 ", sc) and "--require-identical" in sc and "--usd-per-hour 0.56" in sc
print(f"accounting ok: soft {soft}s, hard {hard}s, prior-usd {prior} (raw {raw:.5f}), started = request time")
PYC
# The generated remote script, executed under a scratch root with a stub driver (churn r1): every classification, the
# driver's calls in order, and the STOP file.
ran=$((ran+1)); echo "== the generated remote script with a stub driver (churn r1)"
mkdir -p stubbin junk
printf '%s\n' '#!/bin/bash' \
  '# stub for `uv run --frozen python <driver> ...`: logs the call, then acts as $STUB says ("gate=cap", "search=crash", ...)' \
  'echo "$*" >> "$REMOTE_ROOT/calls.log"' \
  'what=gate; prev=""; for i in "$@"; do [ "$prev" = "--stage" ] && what=$i; prev=$i; done' \
  'case " $STUB " in' \
  '  *" $what=cap "*) echo "SystemExit: churn arm stopped between stages: 4.10 USD billed + 1.00 USD for the next stage would pass the 5.00 USD cap"; exit 1 ;;' \
  '  *" $what=fail "*) echo "{\"gate_ok\": false}"; echo "churn arm stopped: the p = 0 gate failed"; exit 1 ;;' \
  '  *" $what=crash "*) echo "Traceback (most recent call last): ValueError"; exit 1 ;;' \
  'esac; exit 0' > stubbin/uv
chmod +x stubbin/uv
rcheck() { # STUB expected-last-line [STOPFILE]
  rr=$(mktemp -d); mkdir -p $rr/touchstone/results/logs $rr/bundle $rr/.local/bin; cp stubbin/uv $rr/.local/bin/uv; [ -n "${3:-}" ] && touch $rr/STOP
  last=$(REMOTE_ROOT=$rr HOME=$rr STUB="$1" bash pushed_r_remote.sh 2>&1 | tail -n 1)
  echo "$last" | grep -Eq "^$2 [0-9]{2}:[0-9]{2}\$" || { echo "SCENARIO FAILED (remote, STUB='$1': last line '$last', expected '$2')"; fail=1; }
  RCALLS=$(cat $rr/calls.log 2>/dev/null); mv -- $rr junk/rr.$RANDOM; }
rcheck "gate=cap" "== STOPPED BEFORE gate \(cap, driver admission\)"
rcheck "gate=fail" "== GATE FAILED"
rcheck "gate=crash" "== RUN FAILED at gate"
rcheck "search=cap" "== STOPPED BEFORE search \(cap, driver admission\)"
rcheck "freeze=crash" "== RUN FAILED at freeze"
rcheck "" "== STOPPED BEFORE gate \(cap\)" stop
rcheck "" "== RUN OK"
python3 - "$RCALLS" <<'PYR' || { echo "SCENARIO FAILED (remote driver calls)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]
assert len(c) == 8, len(c)
assert all(x[:4] == ["run", "--frozen", "python", "docs/revision/churn/churn_v2.py"] for x in c)
g = " ".join(c[0]); assert "--gate only" in g and "--require-identical" in g and "--out results/v2/followup-churn" in g and "--stage" not in g
st = [x[x.index("--stage") + 1] for x in c[1:]]; assert st == ["inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory"], st
for x in c[1:]:
    j = " ".join(x); assert "--workers-search 16" in j and "--workers-eval 9" in j and "--require-identical" in j and "--out results/v2/followup-churn" in j
print("remote ok: 7 classifications, gate then 7 stages with the expected flags")
PYR
cd /; mv -- $H ~/.Trash/harness_$$
# a filtered (ONLY) run can never pass: the gate needs every scenario (r16)
if [ $fail != 0 ]; then echo "HARNESS FAILED"; exit 1; elif [ $ran != $TOTAL ]; then echo "HARNESS PARTIAL ($ran of $TOTAL scenarios ran)"; exit 2; else echo "HARNESS OK ($ran of $TOTAL scenarios)"; fi
