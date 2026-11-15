#!/bin/bash
# Offline harness for followup2_pod.sh (Runs A and B; derived from test_churn_pod_harness.sh) with podctl.py and fake
# runpod.py / create_one.py (no real pods). The fakes keep pods, pending (delayed) creations and stuck deletions in
# state.json under an exclusive lock (r15). Each pod scenario asserts: the pods left (0), the exact number of creation
# requests, the launcher exit status, the end state (an anchored pattern), that the watchdog ended by itself (unless the
# scenario expects it to stay, fail-closed) and released the launch lock, and, where stated, a watchdog log line, a
# launcher output line, and a line that must not appear (NOTOUT). The pre-pod path (guards, lock, creation, price,
# watchdog, deletion) is shared by both runs and is exercised with Run A; Run B gets its own guard, RUN OK and end-state
# scenarios. The generated remote scripts of both runs are executed under a scratch root with a stub `uv` for every end
# state, and the embedded verifier is run on prepared directories.
set -u; H=$(mktemp -d); cd $H; SRC=/Users/oemer.demirel/Projects/touchstone/results/pods
python3 $SRC/case_end_check.py $SRC/followup2_pod.sh || { echo "HARNESS FAILED (a case branch ends inside a comment)"; exit 1; }
sed "s#P=/Users/oemer.demirel/Projects/touchstone/results/pods#P=$H#; s#snapf=\"/Users/oemer.demirel/Projects/touchstone/results/pods/snap_#snapf=\"$H/snap_#; s#^PY=/opt/homebrew/bin/python3;#PY=$H/pywrap;#" $SRC/followup2_pod.sh > followup2_pod.sh
grep -q "^PY=$H/pywrap;" followup2_pod.sh || { echo "HARNESS FAILED (python wrapper not installed)"; exit 1; }
printf '%s\n' '#!/bin/bash' '# holds a launch with F2HOLD=1 at its tarball guard while hold_guard exists (review r2 scenario)' \
  'case "$*" in *tarfile*getmembers*) [ -n "${F2HOLD:-}" ] && while [ -e "$(dirname "$0")/hold_guard" ]; do sleep 1; done ;; esac' \
  'exec /opt/homebrew/bin/python3 "$@"' > pywrap; chmod +x pywrap
cp $SRC/podctl.py .
mkdir -p g && (cd g && git init -q && git -c commit.gpgsign=false -c user.email=x@x -c user.name=x commit -q --allow-empty -m x && git -c tag.gpgsign=false tag protocol-v2 && COPYFILE_DISABLE=1 tar --uid 0 --gid 0 -czf ../c.tgz .)
C=$(git -C g rev-parse HEAD); export HC=$C
export WT=/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 REALUV=$(command -v uv) REALCACHE=$(uv cache dir 2>/dev/null)
# bundles: the evidence each run needs (Run B's Mac gate records bound to the commit); a variant bound to another commit
python3 - "$C" <<'EOF'
import json, os, sys
c = sys.argv[1]
for root, commit in (("bun", c), ("bunbad", "0" * 40)):
    for p, d in (("evidence/a-gate-repro/gate.json", {"stage": "reproduction gate", "pass": True}),
                 ("evidence/a-gate-dbl/gate.json", {"stage": "doubling gate", "pass": True}),
                 ("evidence/conv-gate-mac/headline@rho0.2__F111__X7-SC__profit__mac.json", {"site": "mac", "pass": True, "binding": {"provenance": {"git_commit": commit}}}),
                 ("evidence/conv-gate-mac/fresh1@rho0.2__F111__D2+H3__profit__mac.json", {"site": "mac", "pass": True, "binding": {"provenance": {"git_commit": commit}}})):
        os.makedirs(os.path.dirname(f"{root}/{p}"), exist_ok=True); json.dump(d, open(f"{root}/{p}", "w"))
EOF
(cd bun && tar czf ../b.tgz .); (cd bunbad && tar czf ../bbad.tgz .)
# prepared remote outputs with complete inventories, for the RUN OK scenarios
python3 - <<'EOF'
import hashlib, json, os
for d in ("remote/followup2-a-pod-gate", "remote/followup2-runnerup", "remote/followup2-conv"):
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
            led = json.load(open(os.path.join(H, "ledger.json"))); led["spent"].append({"op": "followup", "tag": "runner-up-late", "usd": 9.0})
            json.dump(led, open(os.path.join(H, "ledger.json"), "w"))
        print(f"git={os.environ.get('HC','')} env=unset bundle=6 memgb=64 py=x")
    elif "tail -c 240" in c: print("== remote started 11:48 == reset gate start 11:48 == RUN OK 12:00" if st.get("runok") else st.get("remote_tail", "== remote started 11:48 == runner-up start 11:50"))
    else: print("up")
elif cmd == "push":
    if st.get("push_fail"): rc = 1; print("exit 1")
    else:
        b = os.path.basename(a[2])
        if b in ("r_remote.sh", "f2.attempts", "f2.ledger.json"): shutil.copy(a[1], os.path.join(H, "pushed_" + b))   # kept for the checks
        print("exit 0")
elif cmd == "pull":
    src, dst = a[1], a[2]
    for k in ("followup2-a-pod-gate", "followup2-runnerup", "followup2-conv"):
        if k in src:
            shutil.copytree(os.path.join(H, "remote", k), dst, dirs_exist_ok=True)
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
    p = os.getppid(); top = None   # the topmost process running the launcher snapshot (subshells share its command line)
    while p > 1:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(p)], capture_output=True, text=True).stdout
        if "snap_followup2_pod" in cmd: top = p
        p = int(subprocess.run(["ps", "-o", "ppid=", "-p", str(p)], capture_output=True, text=True).stdout.strip() or 1)
    if top: os.kill(top, signal.SIGTERM)
    sys.exit(1)
print(json.dumps({"id": "" if amb else pid, "ambiguous": amb, "vcpu": 16}))
EOF
# ledger: LEDGERV selects a variant; reservations cover the watchdog bound of each run at its plan cap
ledger() { python3 - "$1" "${2:-0}" <<'EOF'
import json, sys
v, prior = sys.argv[1], float(sys.argv[2])
d = {"caps": {"followup": 72.0}, "reservations": [{"op": "followup", "tag": "runner-up-t", "cap": 3.9}, {"op": "followup", "tag": "convergence2-t", "cap": 5.525}],
     "spent": [{"op": "followup", "tag": "reset-pod", "usd": 1.65}, {"op": "followup", "tag": "churn-pod", "usd": 4.99}]}
if prior:
    d["spent"].append({"op": "followup", "tag": "runner-up-0", "usd": prior})
if v == "nores":
    d["reservations"] = [{"op": "followup", "tag": "runner-up-t", "cap": 3.0}]          # the stop cap only: below the bound
if v == "wrongop":
    d["reservations"] = [{"op": "development", "tag": "runner-up-t", "cap": 3.9}]       # another category (review r1, Astra 1)
if v == "leftover":
    d["reservations"].append({"op": "followup", "tag": "runner-up-0", "cap": 3.9})     # an earlier launch, spend not recorded
if v == "tagu":
    d["reservations"] = [{"op": "followup", "tag": "runner-up-u", "cap": 3.9}]
if v == "reused":
    d["spent"].append({"op": "followup", "tag": "runner-up-t", "usd": 0.5})            # this launch tag already spent
if v == "badrow":
    d["spent"].append({"op": "followup", "tag": "runner-up-x", "usd": float("nan")})
open("ledger.json", "w").write(json.dumps(d))
EOF
}
fail=0; ran=0; TOTAL=39
run() { # name state cap creates rc [end-pattern] [watchdog-log-substring] [launcher-output-substring]; env RUNV (A), BUN
  [ -n "${ONLY:-}" ] && ! echo "$1" | grep -q "$ONLY" && return 0   # smoke runs only; a full run sets no ONLY
  r=${RUNV:-A}; rl=$(echo $r | tr AB ab); T=${TAGV:-t}; N=ts-f2$rl; LG=logs_f2${rl}_$T
  ran=$((ran+1)); echo "== $1"; echo "$2" > state.json; mkdir -p $LG junk; : > $LG/watchdog.log; : > $N.wdpid
  for f in $N.bal0 $N.spent $N.wdend; do [ -e $f ] && mv -- $f junk/$f.$ran; done   # isolation: one launch per scenario
  [ -n "${PRELOCK:-}" ] && mkdir $N.launchlock
  [ -n "${PREBAL:-}" ] && echo "100.0 0.0" > $N.bal0
  [ -n "${EMPTYSPENT:-}" ] && : > $N.spent
  ledger "${LEDGERV:-ok}" "${PRIORV:-0}"
  if [ -n "${PRIORENV:-}" ]; then
    PRIOR=$PRIORENV EXPECT=$C MAXCPH=0.70 HARD=${HARDX:-1.3} LEDGER=$H/ledger.json DRYRUN=${DRY:-} perl -e 'alarm 1500; exec @ARGV' bash followup2_pod.sh $r c.tgz ${BUN:-b.tgz} $T $3 out > run.out 2>&1; lrc=$?
  else
    EXPECT=$C MAXCPH=0.70 HARD=${HARDX:-1.3} LEDGER=$H/ledger.json DRYRUN=${DRY:-} perl -e 'alarm 1500; exec @ARGV' bash followup2_pod.sh $r c.tgz ${BUN:-b.tgz} $T $3 out > run.out 2>&1; lrc=$?
  fi
  out=$(grep -v "^tarball\|code guard\|bundle guard\|^ledger:" run.out); echo "$out" | tail -3
  # wait for THIS scenario's watchdog by its PID (r11); the settle while a request is pending is 30 minutes
  wd=$(cat $N.wdpid 2>/dev/null); alive=""
  for i in $(seq 1 ${WAITW:-800}); do [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null || break; sleep 3; done
  if [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null; then alive=1; kill "$wd"; sleep 1; echo "watchdog $wd still running; stopped"; fi
  read left creates <<< "$(python3 -c "import json;s=json.load(open('state.json'));print(len(s['pods'])+len(s.get('pending',{})), sum(1 for l in s['log'] if l.startswith('create')))")"
  echo "pods left: $left, creation requests: $creates (expected $4), exit $lrc (expected $5)"; tail -1 $LG/watchdog.log
  [ "$left" = 0 ] && [ "$creates" = "$4" ] && [ "$lrc" = "$5" ] || { echo "SCENARIO FAILED"; fail=1; }
  [ -z "${6:-}" ] || echo "$out" | grep -Eq "^[0-9]{2}:[0-9]{2} end: ($6)\$" || { echo "SCENARIO FAILED (end line is not: $6)"; fail=1; }
  [ -z "${7:-}" ] || grep -q "$7" $LG/watchdog.log || { echo "SCENARIO FAILED (watchdog log lacks: $7)"; fail=1; }
  [ -z "${8:-}" ] || echo "$out" | grep -Eq "$8" || { echo "SCENARIO FAILED (launcher output lacks: $8)"; fail=1; }
  [ -z "${NOTOUT:-}" ] || ! { echo "$out"; cat $LG/watchdog.log; } | grep -q "$NOTOUT" || { echo "SCENARIO FAILED (output contains: $NOTOUT)"; fail=1; }
  if [ -n "${WD_ALIVE:-}" ]; then [ -n "$alive" ] || { echo "SCENARIO FAILED (the watchdog should have stayed, fail-closed)"; fail=1; }
  elif [ -n "$alive" ]; then echo "SCENARIO FAILED (the watchdog did not end by itself)"; fail=1; fi
  if [ -z "${PRELOCK:-}" ] && [ -z "$alive" ] && [ -d $N.launchlock ]; then echo "SCENARIO FAILED (launch lock not released)"; fail=1; fi
  [ -z "${PREBAL:-}" ] || [ -e $N.bal0 ] || { echo "SCENARIO FAILED (the previous spend baseline was not kept)"; fail=1; }
  python3 podctl.py unlock $N >/dev/null 2>&1; true; }   # test isolation only (a held or stale lock)
# --- refusals before any marker (new for follow-up 2)
RUNV=C run "an unknown run letter is refused" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: the run must be A or B"
PRIORENV=1 run "PRIOR from the environment is refused (it comes from the ledger)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: PRIOR is not an input here"
run "a cap above the plan's is refused" '{"pods":{},"price":0.56,"up":true,"log":[]}' 5 0 1 "" "" "^refused: the cap must be positive and at most the plan's 3.00 USD"
LEDGERV=nores run "a reservation below the watchdog bound is refused" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: no single followup reservation runner-up-t covers the watchdog bound 3.9000 USD"
LEDGERV=wrongop run "a reservation in another category is refused (r1)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: no single followup reservation runner-up-t covers"
LEDGERV=leftover run "an open reservation of an earlier launch refuses the launch (r1)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: open reservations \\['runner-up-0'\\] of runner-up"
LEDGERV=reused run "a launch tag that already has a spend record is refused (r1)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: runner-up-t already has a spend record"
PRELOCK=1 TAGV=u LEDGERV=tagu run "the run-level lock refuses a launch of the same run under another tag (r1)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^LOCKED: ts-f2a.launchlock exists"
LEDGERV=badrow run "a malformed ledger row is refused" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: a malformed spend row in the ledger"
RUNV=B BUN=bbad.tgz run "Run B is refused when its Mac gate records are not bound to EXPECT" '{"pods":{},"price":0.56,"up":true,"log":[]}' 4.25 0 1 "" "" "^bundle refused"
RUNV=B DRY=1 run "Run B dry run: every guard passes, no pod" '{"pods":{},"price":0.56,"up":true,"log":[]}' 4.25 0 0 "" "" "^dry run: guards passed; no pod created"
# --- review r2 (Sol 1): a second launch of the same run and tag, held before the lock while the first launch runs, ends
# and has its spend recorded (the ledger replaces the reservation by a spend row), must be refused when it resumes: it
# reads the ledger only under the lock. Before the fix it had validated the stale ledger and created a second pod.
ran=$((ran+1)); echo "== a second launch held before the lock validates the ledger as it is under the lock (r2)"
echo '{"pods":{},"price":0.9,"up":true,"log":[]}' > state.json; mkdir -p logs_f2a_t junk; : > logs_f2a_t/watchdog.log; : > ts-f2a.wdpid
for f in ts-f2a.bal0 ts-f2a.spent ts-f2a.wdend; do [ -e $f ] && mv -- $f junk/$f.r2; done
ledger ok 0; touch hold_guard; rm -f run2.rc
( F2HOLD=1 EXPECT=$C MAXCPH=0.70 LEDGER=$H/ledger.json bash followup2_pod.sh A c.tgz b.tgz t 3 out2 > run2.out 2>&1; echo $? > run2.rc ) &
sleep 5
EXPECT=$C MAXCPH=0.70 LEDGER=$H/ledger.json perl -e 'alarm 1500; exec @ARGV' bash followup2_pod.sh A c.tgz b.tgz t 3 out > run.out 2>&1; l1=$?
wd=$(cat ts-f2a.wdpid 2>/dev/null); for i in $(seq 1 800); do [ -n "$wd" ] && kill -0 "$wd" 2>/dev/null || break; sleep 3; done
echo "0.012 USD balance difference (test)" > ts-f2a.spent                    # podctl.py spend, then the ledger record
python3 - <<'PYR'
import json
d = json.load(open("ledger.json")); d["reservations"] = [r for r in d["reservations"] if r["tag"] != "runner-up-t"]
d["spent"].append({"op": "followup", "tag": "runner-up-t", "usd": 0.012}); json.dump(d, open("ledger.json", "w"))
PYR
mv -- hold_guard junk/hold_guard.r2
for i in $(seq 1 400); do [ -e run2.rc ] && break; sleep 3; done
wd2=$(cat ts-f2a.wdpid 2>/dev/null); for i in $(seq 1 800); do [ -n "$wd2" ] && kill -0 "$wd2" 2>/dev/null || break; sleep 3; done
creates=$(python3 -c "import json;s=json.load(open('state.json'));print(sum(1 for l in s['log'] if l.startswith('create')))")
echo "first launch exit $l1; second launch exit $(cat run2.rc 2>/dev/null); creation requests $creates (expected 1)"; grep -E "^refused|end:" run2.out | tail -2
{ [ "$l1" = 1 ] && [ "$(cat run2.rc 2>/dev/null)" = 1 ] && [ "$creates" = 1 ] && grep -q "^refused: runner-up-t already has a spend record" run2.out; } || { echo "SCENARIO FAILED (delayed second launch)"; fail=1; }
[ -d ts-f2a.launchlock ] && { echo "SCENARIO FAILED (launch lock not released)"; fail=1; }
python3 podctl.py unlock ts-f2a >/dev/null 2>&1; [ -e ts-f2a.spent ] && mv -- ts-f2a.spent junk/ts-f2a.spent.r2b; [ -e ts-f2a.bal0 ] && mv -- ts-f2a.bal0 junk/ts-f2a.bal0.r2b; true
# --- the shared pre-pod path (from the churn harness), with Run A
NOTOUT="pull or verification failed" run "price above the ceiling: deleted at once, no retrieval" '{"pods":{},"price":0.9,"up":true,"log":[]}' 3 1 1 "PRICE 0.9 NOT IN \(0, 0.70\]"
NOTOUT="pull or verification failed" run "null price: deleted at once (r12)" '{"pods":{},"price":null,"up":true,"log":[]}' 3 1 1 "PRICE unknown NOT IN \(0, 0.70\]"
run "an ambiguous answer ends creation: one request, no retry" '{"pods":{},"price":0.56,"up":true,"log":[],"lose":true}' 3 1 1 "AMBIGUOUS CREATION ANSWER \(no retry\)" "for 1800s" "UNRESOLVED"
run "a pod created long after an ambiguous answer (beyond 300 s) is deleted by the watchdog" '{"pods":{},"price":0.56,"up":true,"log":[],"lose":true,"delay":20}' 3 1 1 "AMBIGUOUS CREATION ANSWER \(no retry\)" "WATCHDOG: deleting"
run "a stop during creation leaves the request pending; the late pod is deleted (r15)" '{"pods":{},"price":0.56,"up":true,"log":[],"term":true,"delay":20}' 3 1 1 "NOT STARTED" "for 1800s" "outstanding or ambiguous"
HARDX=1.0 run "unreachable pod at the deadline" '{"pods":{},"price":0.56,"up":false,"log":[]}' 0.004 1 1 "CREATION BLOCKED \(hard deadline\)|SOFT DEADLINE BEFORE START|NO POD"
HARDX=1.0 run "deletion keeps failing: the watchdog deletes after the deadline" '{"pods":{},"price":0.56,"up":false,"log":[],"stuck_next":true}' 0.004 1 1 "UNREACHABLE POD NOT DELETED|CREATION BLOCKED \(hard deadline\)|SOFT DEADLINE BEFORE START|NO POD" "WATCHDOG: deleting"
WD_ALIVE=1 WAITW=20 run "listing always fails: no creation; the watchdog stays (fail-closed)" '{"pods":{},"price":0.56,"up":true,"log":[],"fail_list":1000000}' 3 0 1 "RECONCILE FAILED BEFORE REQUEST 1"
PRELOCK=1 run "a held launch lock refuses the launch (r15)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^LOCKED: ts-f2a.launchlock exists"
PREBAL=1 run "an unrecorded previous spend refuses the launch and keeps its baseline (r16)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: the previous launch's spend is not recorded"
PREBAL=1 EMPTYSPENT=1 run "an empty spend record does not count as recorded (r17)" '{"pods":{},"price":0.56,"up":true,"log":[]}' 3 0 1 "" "" "^refused: the previous launch's spend is not recorded"
run "unknown balance: no creation, lock released (r16)" '{"pods":{},"price":0.56,"up":true,"log":[],"bal_fail":true}' 3 0 1 "" "" "^refused: account balance unknown$"
NOTOUT="pull or verification failed" run "upload failure stops the run before it starts (r15)" '{"pods":{},"price":0.56,"up":true,"log":[],"push_fail":true}' 3 1 1 "UPLOAD FAILED \(code\)"
run "Run A: RUN OK with one corrupt pull, retried until both directories verify; a ledger edit after the deadlines does not reach the pod" '{"pods":{},"price":0.56,"up":true,"log":[],"runok":true,"corrupt_pulls":1,"mutate_ledger":true}' 3 1 0 "RUN OK" "" "verify followup2-runnerup: 2 records, 0 bad, 0 not inventoried"
cp pushed_r_remote.sh pushed_A.sh
python3 - <<'PYS' || { echo "SCENARIO FAILED (ledger snapshot)"; fail=1; }
import json
now, pushed = json.load(open("ledger.json")), json.load(open("pushed_f2.ledger.json"))
assert any(r["tag"] == "runner-up-late" for r in now["spent"]) and not any(r["tag"] == "runner-up-late" for r in pushed["spent"]), "the pushed ledger is not the validated snapshot"
print("ledger snapshot ok: the pushed copy is the one validated before the deadlines")
PYS
run "Run A: the end state is the last line of the polled tail (a gate failure after earlier lines)" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== remote started 11:48 == reset gate start 11:48 == GATE FAILED at reset gate (not bit-identical) 12:00"}' 3 1 1 "== GATE FAILED at reset gate \(not bit-identical\) 12:00"
run "Run A: the driver's cap admission stops the run between stages" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== reset gate passed (bit-identical) 12:30 == runner-up start 12:30 == STOPPED BEFORE search (cap, driver admission) 12:40"}' 3 1 1 "== STOPPED BEFORE search \(cap, driver admission\) 12:40"
RUNV=B run "Run B: RUN OK with one corrupt pull, retried until verified" '{"pods":{},"price":0.56,"up":true,"log":[],"runok":true,"corrupt_pulls":1}' 4.25 1 0 "RUN OK" "" "verify followup2-conv: 2 records, 0 bad, 0 not inventoried"
cp pushed_r_remote.sh pushed_B.sh
# Run B rerun: records are verified on every end state, not only after RUN OK (lessons.md); a failed check after a non-OK
# end is reported once, without the RUN OK retry loop; a bad worker count is refused before any marker.
RUNV=B run "Run B: records pulled after a stop are verified too" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== remote started 11:48 == convergence start 12:00 == RUN FAILED at convergence 13:00"}' 4.25 1 1 "== RUN FAILED at convergence 13:00" "" "verify followup2-conv: 2 records, 0 bad, 0 not inventoried"
RUNV=B run "Run B: a corrupt pull after a stop is reported once, not retried" '{"pods":{},"price":0.56,"up":true,"log":[],"corrupt_pulls":5,"remote_tail":"== remote started 11:48 == convergence start 12:00 == RUN FAILED at convergence 13:00"}' 4.25 1 1 "== RUN FAILED at convergence 13:00" "" "end state == RUN FAILED at convergence 13:00: pulled records do not all verify"
CONVWORKERS=0 RUNV=B run "Run B: a worker count outside 1 to 16 is refused" '{"pods":{},"price":0.56,"up":true,"log":[]}' 4.25 0 1 "" "" "^refused: CONVWORKERS must be an integer from 1 to 16"
RUNV=B run "Run B: a failed convergence gate is the end state" '{"pods":{},"price":0.56,"up":true,"log":[],"remote_tail":"== remote started 11:48 == convergence gate start 11:48 == GATE FAILED at convergence gate (round 1 differs from the registered record) 13:00"}' 4.25 1 1 "== GATE FAILED at convergence gate \(round 1 differs from the registered record\) 13:00"
# Accounting: the ledger records 1.2 USD for runner-up (PRIOR), and a first pod never answers (deleted after 240 s). The
# deadlines leave CAP - PRIOR and HARD x CAP - PRIOR; the pushed attempts file has the deleted attempt and exactly one open
# start, the live pod's request time, which is --started-at; the admission flags carry the plan cap, the ceiling, the run
# tag, the pushed ledger and attempts, the STOP file and the soft deadline.
PRIORV=1.2 run "Run A: ledger PRIOR and a deleted attempt count against the deadlines and the admission inputs" '{"pods":{},"price":0.56,"up":true,"log":[],"down_first":true,"remote_tail":"== STOPPED BEFORE reset gate (cap, admission) 12:00"}' 3 2 1 "== STOPPED BEFORE reset gate \(cap, admission\) 12:00"
python3 - "$H" <<'PYC' || { echo "SCENARIO FAILED (accounting)"; fail=1; }
import json, re, sys
H = sys.argv[1]; out = open(f"{H}/run.out").read(); sc = open(f"{H}/pushed_r_remote.sh").read()
st = json.load(open(f"{H}/state.json")); att = [l.split() for l in open(f"{H}/pushed_f2.attempts")]
m = re.search(r"soft stop in (\d+)s, hard stop in (\d+)s", out); soft, hard = int(m[1]), int(m[2])
assert int(3600 * 1.8 / 0.70) - 900 < soft <= int(3600 * 1.8 / 0.70) and hard <= int(3600 * (3.9 - 1.2) / 0.70), (soft, hard)
starts = {f[0]: int(f[1]) for f in att if f[2] == "start"}; dels = {f[0]: int(f[1]) for f in att if f[2] == "deleted"}
(p1, c1), (p2, c2) = st["created"][0], st["created"][1]
assert set(starts) == {p1, p2} and set(dels) == {p1} and dels[p1] - starts[p1] >= 240 and starts[p1] <= c1, (starts, dels)
paid = re.search(r'PAID="([^"]*)"', sc)[1]
started = int(re.search(r"--started-at (\d+)", paid)[1]); assert started == starts[p2] and started <= c2, (started, starts, c2)
for f in ("--cap-usd 3 ", "--usd-per-hour 0.70 ", "--run-tag runner-up ", "--attempts $R/f2.attempts", "--ledger $R/f2.ledger.json", "--stop-file $R/STOP"):
    assert f in paid + " ", f
sd = int(re.search(r"--soft-deadline (\d+)", paid)[1]); assert abs((sd - started) - soft) < 60, (sd, started, soft)
led = json.load(open(f"{H}/pushed_f2.ledger.json")); assert any(r["tag"] == "runner-up-0" and r["usd"] == 1.2 for r in led["spent"])
assert "ledger: PRIOR 1.2 USD recorded for runner-up" in out
print(f"accounting ok: soft {soft}s, hard {hard}s, PRIOR 1.2 from the ledger, one open attempt = --started-at")
PYC
cp pushed_r_remote.sh pushed_acct.sh; cp pushed_f2.attempts acct.attempts; cp pushed_f2.ledger.json acct.ledger.json
# The generated remote scripts, executed under a scratch root with a stub `uv` (logs each call; acts as $STUB says):
# every end state, the order of calls (admission before each paid step, the gate before the driver), and the flags.
mkdir -p stubbin junk
cat > stubbin/uv <<'EOF'
#!/bin/bash
# stub for `uv run --frozen python <script> ...`. STUB words: admit@<hours>=refuse|crash, gate=fail|crash|cap, run=cap|fail|crash
echo "$*" >> "$REMOTE_ROOT/calls.log"
if [ -n "${REALADMIT:-}" ] && [ "${4##*/}" = guards.py ]; then         # the real admission, not a stub exit code (review r1)
  cd "$WT" && UV_CACHE_DIR="$REALCACHE" exec "$REALUV" run --frozen python docs/revision/followup2/guards.py "${@:5}"
fi
s=$4; what=run; hours=""; prev=""
for i in "$@"; do [ "$prev" = "--hours" ] && hours=$i; prev=$i; done
case "$s" in *guards.py) what="admit@$hours" ;; *reset_followup_v2.py) what=gate ;; *convergence_v2.py) case " $* " in *" --gate "*) what=gate ;; esac ;; esac
act=""; for w in $STUB; do [ "${w%%=*}" = "$what" ] && act=${w#*=}; done
case "$what:$act:$s" in
  admit*:refuse:*) echo '{"stopped_before": "next step"}'; exit 3 ;;
  admit*:crash:*) echo "follow-up refused: no launcher attempts file"; exit 1 ;;
  gate:fail:*reset_followup_v2.py) echo '{"reproduce": "x", "require_identical": true, "gate_ok": false}'; exit 1 ;;
  gate:fail:*) exit 4 ;;
  gate:cap:*) exit 3 ;;
  *:crash:*) echo "Traceback (most recent call last): ValueError"; exit 1 ;;
  run:cap:*) echo '{"stopped_before": "search", "cap_usd": 3.0}'; exit 3 ;;
  run:fail:*) exit 4 ;;
  run:lost:*) exit 5 ;;                                            # a worker lost (Run B rerun), every time
  run:lostonce:*) [ -e "$REMOTE_ROOT/lost1" ] && exit 0; touch "$REMOTE_ROOT/lost1"; exit 5 ;;
esac
exit 0
EOF
chmod +x stubbin/uv
rcheck() { # SCRIPT STUB expected-last-line [STOPFILE]; env REALADMIT: the real guards.py with the accounting launch's pushed files
  rr=$(mktemp -d); mkdir -p $rr/touchstone/results/logs $rr/bundle $rr/.local/bin; cp stubbin/uv $rr/.local/bin/uv; [ -n "${4:-}" ] && touch $rr/STOP
  [ -n "${REALADMIT:-}" ] && { cp acct.attempts $rr/f2.attempts; cp acct.ledger.json $rr/f2.ledger.json; }
  last=$(REMOTE_ROOT=$rr HOME=$rr STUB="$2" bash $1 2>&1 | tail -n 1)
  echo "$last" | grep -Eq "^$3 [0-9]{2}:[0-9]{2}\$" || { echo "SCENARIO FAILED (remote $1, STUB='$2': last line '$last', expected '$3')"; fail=1; }
  RCALLS=$(cat $rr/calls.log 2>/dev/null); RADMIT=$(cat $rr/touchstone/results/logs/f2_admit.log 2>/dev/null); mv -- $rr junk/rr.$RANDOM; }
ran=$((ran+1)); echo "== Run A: the generated remote script with a stub driver"
rcheck pushed_A.sh "admit@0.61=refuse" "== STOPPED BEFORE reset gate \(cap, admission\)"
rcheck pushed_A.sh "admit@0.61=crash" "== RUN FAILED at admission before reset gate"
rcheck pushed_A.sh "gate=fail" "== GATE FAILED at reset gate \(not bit-identical\)"
rcheck pushed_A.sh "gate=crash" "== RUN FAILED at reset gate"
rcheck pushed_A.sh "admit@2.65=refuse" "== STOPPED BEFORE runner-up \(cap, admission\)"
rcheck pushed_A.sh "run=cap" "== STOPPED BEFORE search \(cap, driver admission\)"
rcheck pushed_A.sh "run=crash" "== RUN FAILED at runner-up"
rcheck pushed_A.sh "" "== STOPPED BEFORE reset gate \(cap\)" stop
rcheck pushed_A.sh "" "== RUN OK"
python3 - "$RCALLS" <<'PYR' || { echo "SCENARIO FAILED (Run A remote calls)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]
assert [x[3] for x in c] == ["docs/revision/followup2/guards.py", "docs/revision/followup/reset_followup_v2.py", "docs/revision/followup2/guards.py", "docs/revision/followup2/runnerup_v2.py"], [x[3] for x in c]
assert all(x[:3] == ["run", "--frozen", "python"] for x in c)
j = [" ".join(x) for x in c]
assert j[0].split()[4] == "admit" and "--hours 0.61" in j[0] and "--hours 2.65" in j[2]
for k in (0, 2, 3):
    for f in ("--cap-usd 3 ", "--usd-per-hour 0.70 ", "--run-tag runner-up ", "/f2.attempts ", "/f2.ledger.json ", "/STOP ", "--soft-deadline ", "--started-at "):
        assert f in j[k] + " ", (k, f)
assert "--reproduce --require-identical --out results/v2/followup2-a-pod-gate" in j[1] and "/bundle/eval-all" in j[1] and "--report " in j[1]
for f in ("--stage all", "--workers 12", "--site pod", "--out results/v2/followup2-runnerup", "/bundle/evidence/a-gate-repro", "--reset-pod results/v2/followup2-a-pod-gate", "/bundle/evidence/a-gate-dbl", "/bundle/report/report.json"):
    assert f in j[3], f
print("remote ok (A): 9 end states; admit, gate, admit, driver, with the expected flags")
PYR
ran=$((ran+1)); echo "== Run B: the generated remote script with a stub driver"
rcheck pushed_B.sh "admit@1.06=refuse" "== STOPPED BEFORE convergence gate \(cap, admission\)"
rcheck pushed_B.sh "gate=cap" "== STOPPED BEFORE convergence gate \(cap, driver admission\)"
rcheck pushed_B.sh "gate=fail" "== GATE FAILED at convergence gate \(round 1 differs from the registered record\)"
rcheck pushed_B.sh "gate=crash" "== RUN FAILED at convergence gate"
rcheck pushed_B.sh "admit@5.10=refuse" "== STOPPED BEFORE convergence \(cap, admission\)"
rcheck pushed_B.sh "run=fail" "== GATE FAILED at convergence \(round 1 differs\)"
rcheck pushed_B.sh "run=crash" "== RUN FAILED at convergence"
rcheck pushed_B.sh "run=lost" "== RUN FAILED at convergence \(a worker lost twice; saved cells kept\)"
rcheck pushed_B.sh "" "== STOPPED BEFORE convergence gate \(cap\)" stop
rcheck pushed_B.sh "" "== RUN OK"
python3 - "$RCALLS" <<'PYR' || { echo "SCENARIO FAILED (Run B remote calls)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]
assert [x[3] for x in c] == ["docs/revision/followup2/guards.py", "docs/revision/followup2/convergence_v2.py"] * 2, [x[3] for x in c]
j = [" ".join(x) for x in c]
assert "--hours 1.06" in j[0] and "--hours 5.10" in j[2]
for k in (0, 1, 2, 3):
    for f in ("--cap-usd 4.25 ", "--usd-per-hour 0.70 ", "--run-tag convergence2 ", "/f2.attempts ", "/f2.ledger.json ", "/STOP ", "--soft-deadline "):
        assert f in j[k] + " ", (k, f)
assert "--gate --site pod --cells headline@rho0.2|F111|X7-SC|profit,fresh1@rho0.2|F111|D2+H3|profit --out results/v2/followup2-conv" in j[1], j[1]
assert "--gate" not in c[3] and "--workers 7" in j[3] and "--out results/v2/followup2-conv" in j[3]
ev = [c[3][i + 1] for i, x in enumerate(c[3]) if x == "--evidence"]
assert len(ev) == 4 and sum("/bundle/evidence/conv-gate-mac/" in e for e in ev) == 2 and sum(e.startswith("results/v2/followup2-conv/gate/") and e.endswith("__pod.json") for e in ev) == 2, ev
print("remote ok (B): 10 end states; admit, gate, admit, main run with four evidence records")
PYR
ran=$((ran+1)); echo "== Run B: a lost worker restarts the stage once at half the workers (Run B rerun)"
rcheck pushed_B.sh "run=lostonce" "== RUN OK"
python3 - "$RCALLS" <<'PYL' || { echo "SCENARIO FAILED (Run B restart)"; fail=1; }
import sys
c = [l.split() for l in sys.argv[1].splitlines()]
assert [x[3].split("/")[-1] for x in c] == ["guards.py", "convergence_v2.py"] * 3, c
j = [" ".join(x) for x in c]
assert "--hours 2.60" in j[4] and "--workers 7 " in j[3] + " " and "--workers 3 " in j[5] + " " and "--gate" not in c[5], j
print("restart ok: admission, then the stage again with 3 workers")
PYL
rcheck pushed_B.sh "run=lostonce admit@2.60=refuse" "== STOPPED BEFORE convergence restart \(cap, admission\)"
# The real admission (review r1): the accounting launch's script, attempts file and ledger (PRIOR 1.2 of a 3 USD cap), with
# the real guards.py: the reset gate (0.61 h at 0.70) is admitted, the runner-up step (2.65 h) would pass the cap and is
# refused by the real check, so the script stops before it.
ran=$((ran+1)); echo "== the real guards.py admission inside the generated remote script (r1)"
REALADMIT=1 rcheck pushed_acct.sh "" "== STOPPED BEFORE runner-up \(cap, admission\)"
python3 - "$RCALLS" "$RADMIT" <<'PYA' || { echo "SCENARIO FAILED (real admission)"; fail=1; }
import json, sys
c = [l.split() for l in sys.argv[1].splitlines()]
assert [x[3].split("/")[-1] for x in c] == ["guards.py", "reset_followup_v2.py", "guards.py"], c
rep = [json.loads(l) for l in sys.argv[2].splitlines() if l.startswith("{")]
assert len(rep) == 2 and rep[0]["log"][-1]["allowed"] is True and rep[1]["log"][-1]["allowed"] is False, rep
assert rep[1]["prior_usd"] > 1.2 and rep[1]["cap_usd"] == 3.0, rep[1]
print(f"real admission ok: gate admitted, runner-up refused (prior {rep[1]['prior_usd']:.4f} USD incl. the deleted attempt)")
PYA
# The embedded verifier (extracted verbatim from the launcher) on prepared directories: complete, a missing record, a
# changed record, a file outside the inventory, and an empty inventory.
ran=$((ran+1)); echo "== the embedded verifier"
sed -n "/^verify() { \$PY - \"\$1\" <<'PYV'\$/,/^PYV\$/p" followup2_pod.sh | sed '1d;$d' > verify.py
python3 - <<'PYT' || { echo "SCENARIO FAILED (verifier)"; fail=1; }
import hashlib, json, os, shutil, subprocess
def mk(d, files, listed):
    os.makedirs(d, exist_ok=True)
    for k, v in files.items():
        os.makedirs(os.path.dirname(f"{d}/{k}") or d, exist_ok=True); open(f"{d}/{k}", "w").write(v)
    json.dump({"records": {k: hashlib.sha256(files[k].encode()).hexdigest() for k in listed}}, open(f"{d}/inventory.json", "w"))
v = lambda d: subprocess.run(["python3", "verify.py", d], capture_output=True, text=True).returncode
mk("vt/ok", {"a.json": "1", "s/b.json": "2", "x.lock": "l"}, ["a.json", "s/b.json"]); assert v("vt/ok") == 0
mk("vt/miss", {"a.json": "1"}, ["a.json"]); json.dump({"records": {"a.json": hashlib.sha256(b"1").hexdigest(), "gone.json": "0" * 64}}, open("vt/miss/inventory.json", "w")); assert v("vt/miss") == 1
mk("vt/chg", {"a.json": "1"}, ["a.json"]); open("vt/chg/a.json", "w").write("2"); assert v("vt/chg") == 1
mk("vt/extra", {"a.json": "1", "run.json": "{}"}, ["a.json"]); assert v("vt/extra") == 1
mk("vt/empty", {}, []); assert v("vt/empty") == 1
print("verifier ok: complete passes; missing, changed, uninventoried and empty fail")
PYT
cd /; mv -- $H ~/.Trash/harness_f2_$$
# a filtered (ONLY) run can never pass: the gate needs every scenario (r16)
if [ $fail != 0 ]; then echo "HARNESS FAILED"; exit 1; elif [ $ran != $TOTAL ]; then echo "HARNESS PARTIAL ($ran of $TOTAL scenarios ran)"; exit 2; else echo "HARNESS OK ($ran of $TOTAL scenarios)"; fi
