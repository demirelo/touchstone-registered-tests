#!/bin/bash
# Snapshot guard: run a private copy, so an edit to this file cannot reach a running launch.
if [ -z "${LAUNCH_SNAPSHOT:-}" ]; then
  snapf="/Users/oemer.demirel/Projects/touchstone/results/pods/snap_$(basename "$0" .sh)_$$.sh"; cp "$0" "$snapf"
  LAUNCH_SNAPSHOT="$snapf" exec bash "$snapf" "$@"
fi
# Honest-churn arm (docs/revision/churn/churn-plan.md, draft 6) on one Runpod CPU pod: generated from reset_pod.sh after
# its review rounds r9-r18 (pod safety, launch lock, spend records unchanged). Order on the pod: the p = 0 gate through the
# churn path (bit identity, --require-identical; the author's decision), then the 36 churn cells (two rates) stage by
# stage (search with all vCPUs; evaluate, doubling and diagnostics with at most WEVAL workers, the driver's memory
# preflight may choose fewer), then the inventory. The driver also refuses a stage whose admission would pass the cap
# (allocation time, actual price, and PRIOR plus this launch's failed attempts at the ceiling). Spending (the author: do not kill jobs): at the reserved cap the pod stops BETWEEN stages
# (a STOP file the remote script reads before each stage); only at HARD x the cap is the pod deleted mid-stage, as an
# absolute guard. An EXIT/INT/TERM trap pulls what exists (only if the run started), deletes the pod and verifies it.
# Spend (r16): the record is the account balance difference (podctl.py spend NAME, at least an hour after the watchdog
# ends); this launcher prints only estimates. One launch per NAME at a time (NAME.launchlock; the watchdog releases it).
# Usage: churn_pod.sh <code_tgz> <bundle_tgz> <tag> <cap_usd> <local_out>   (no spaces in paths)
# Env: EXPECT (commit inside the code tarball), MAXCPH, optional WEVAL (default 9), MINMEM (default 28), HARD (default 1.3),
# PRIOR (USD recorded for earlier launches of this arm, default 0).
set -u
PY=/opt/homebrew/bin/python3; P=/Users/oemer.demirel/Projects/touchstone/results/pods
TGZ=${1:?code tarball}; BTGZ=${2:?bundle tarball}; TAG=${3:?tag}; CAP=${4:?cap_usd}; LOUT=${5:?local_out}; cd $P
case "$TGZ$BTGZ$TAG$LOUT" in *[[:space:]]*) echo "refused: a path or tag contains whitespace"; exit 1 ;; esac
EXPECT=${EXPECT:?commit}; MAXCPH=${MAXCPH:?max usd per hour}; WEVAL=${WEVAL:-9}; MINMEM=${MINMEM:-28}; HARD=${HARD:-1.3}; PRIOR=${PRIOR:-0}
$PY -c "import math,sys; x=float(sys.argv[1]); sys.exit(0 if math.isfinite(x) and x >= 0 else 1)" "$PRIOR" 2>/dev/null || { echo "refused: PRIOR must be a non-negative number"; exit 1; }
# PRIOR counts against both deadlines (r1 review), so the arm's bound stays HARD x CAP across launches.
$PY -c "import sys; sys.exit(0 if float(sys.argv[1]) < float(sys.argv[2]) else 1)" "$PRIOR" "$CAP" 2>/dev/null || { echo "refused: PRIOR must be below the cap"; exit 1; }
mkdir -p "$LOUT" logs_c_$TAG
$PY -c "import sys,tarfile; ms=tarfile.open(sys.argv[1]).getmembers(); d=[m.name for m in ms if m.name.split('/')[-1].startswith('._')]; o=[m.name for m in ms if m.uid!=0]; print('tarball guard: %d AppleDouble, %d non-root' % (len(d),len(o))); sys.exit(1 if d or o else 0)" "$TGZ" || { echo "code tarball refused"; exit 1; }
hg=$(mktemp -d); tar xzf "$TGZ" -C "$hg" 2>/dev/null || { echo "code tarball refused: cannot unpack"; exit 1; }
# Code guard (fails closed: every git call's status is checked): HEAD is EXPECT, protocol-v2 is an ancestor, the tree is
# clean, every path changed since the tag is in the code freeze's allowed paths, and scripts/, sim/, tests/ equal the tag.
guard() {
  cd "$1" || return 1
  [ "$(git rev-parse HEAD 2>/dev/null)" = "$EXPECT" ] || { echo "HEAD is not $EXPECT"; return 1; }
  git merge-base --is-ancestor protocol-v2 HEAD || { echo "protocol-v2 is not an ancestor"; return 1; }
  st=$(git status --porcelain) || { echo "git status failed"; return 1; }; [ -z "$st" ] || { echo "tree not clean: $st" | head -c 300; return 1; }
  ch=$(git diff --name-only protocol-v2 HEAD) || { echo "git diff failed"; return 1; }
  bad=$(echo "$ch" | grep -v -e '^docs/' -e '^experiments/v2/' -e '^paper/' -e '^sealed2/h4/' -e '^$' || true); [ -z "$bad" ] || { echo "changed outside the allowed paths: $bad" | head -c 300; return 1; }
  git diff --quiet protocol-v2 -- scripts/ sim/ tests/ || { echo "scripts/, sim/ or tests/ differ from protocol-v2"; return 1; }
  echo "code guard: ok at $(git rev-parse --short HEAD)"
}
( guard "$hg" ); g=$?; mv -- "$hg" ~/.Trash/hg_churn_$$
[ $g -eq 0 ] || { echo "code tarball refused"; exit 1; }
[ -n "${DRYRUN:-}" ] && { echo "dry run: guards passed; no pod created"; exit 0; }
# verify DIR: every record in DIR/inventory.json exists with its hash.
verify() { $PY - "$1" <<'PYV'
import hashlib, json, sys
from pathlib import Path
d = Path(sys.argv[1]); inv = json.loads((d / "inventory.json").read_text())
bad = [k for k, h in inv["records"].items() if not (d / k).is_file() or hashlib.sha256((d / k).read_bytes()).hexdigest() != h]
print(f"verify {d.name}: {len(inv['records'])} records, {len(bad)} bad"); sys.exit(1 if bad else 0)
PYV
}
# verify_run FILE STARTED USD_PER_HOUR PRIOR_USD STOP_USD: the driver's run.json (outside the inventories) parses and
# holds exactly the admission inputs this launcher passed (churn launcher review r2).
verify_run() { $PY - "$@" <<'PYR'
import json, math, sys
f, want = sys.argv[1], dict(zip(("started", "usd_per_hour", "prior_usd", "stop_usd"), map(float, sys.argv[2:6])))
try:
    got = json.loads(open(f).read()); ok = set(got) == set(want) and all(math.isclose(float(got[k]), v, abs_tol=1e-9) for k, v in want.items())
except Exception:
    ok = False
print(f"verify run.json: {'ok' if ok else 'bad'}"); sys.exit(0 if ok else 1)
PYR
}
tmo() { perl -e 'alarm shift; exec @ARGV' "$@"; }
NAME=ts-c-$TAG; DONE=$P/$NAME.done; ATT=$P/$NAME.attempts
rm_ok() { [ -e "$1" ] && mv -- "$1" ~/.Trash/"$(basename "$1").$$"; true; }
# One launch per NAME: the lock is taken before any marker changes; the watchdog (the last process) releases it.
mkdir "$P/$NAME.launchlock" 2>/dev/null || { echo "LOCKED: $NAME.launchlock exists (another launch or its watchdog still runs; remove it only after checking)"; exit 1; }
unlock() { $PY podctl.py unlock $NAME >/dev/null 2>&1; }
# Spend records are never overwritten (r16): a launch is refused while the previous launch's spend is unrecorded; a
# recorded one (NAME.spent, written by podctl.py spend) is moved with its inputs to spend_records/NAME.<time>/.
spent_ok() { grep -Eq '^[0-9]+(\.[0-9]+)? USD ' "$P/$NAME.spent" 2>/dev/null; }   # a complete record only (r17)
if [ -e "$P/$NAME.bal0" ] && ! spent_ok; then echo "refused: the previous launch's spend is not recorded (podctl.py spend $NAME)"; unlock; exit 1; fi
if [ -e "$P/$NAME.spent" ] && ! spent_ok; then echo "refused: $NAME.spent is not a complete spend record"; unlock; exit 1; fi
if spent_ok; then
  arch="$P/spend_records/$NAME.$(date +%s)"; mkdir -p "$arch" || { echo "refused: cannot archive the spend record"; unlock; exit 1; }
  for f in bal0 wdend spent attempts; do [ -e "$P/$NAME.$f" ] && { mv -- "$P/$NAME.$f" "$arch/" || { echo "refused: cannot archive $NAME.$f"; unlock; exit 1; }; }; done
fi
for f in "$DONE" "$P/$NAME.blocked" "$P/$NAME.request" "$P/$NAME.wdend" "$P/$NAME.ambiguous" "$P/$NAME.acct" "$P/$NAME.unpriced"; do rm_ok "$f"; done; : > "$ATT"
b0=$(tmo 90 $PY podctl.py balance) || { echo "refused: account balance unknown"; unlock; exit 1; }
echo "$b0" > "$P/$NAME.bal0" && [ -s "$P/$NAME.bal0" ] || { echo "refused: cannot write $NAME.bal0"; unlock; exit 1; }
id=""; state="NOT STARTED"; rc=1; cph=0; a0=0; tfirst=0; unresolved=""; started=""; req=0; wd=""
# Pod safety lives in podctl.py (test_podctl.py): fail-closed listing, deletion verified within
# elapsed time, reconciliation, a creation block from the hard deadline, and a watchdog that runs on after this launcher
# exits, until no pod named $NAME remains.
cleanup() {
  trap - EXIT INT TERM
  if [ -n "$id" ] && [ -n "$started" ]; then
    try=0
    while :; do   # after RUN OK: keep the pod and retry until both directories verify, or until 2 min before the hard deadline
      try=$((try+1)); ok=1
      for d in followup-churn; do
        t=1800
        rem=$(( hard - 120 - $(date +%s) )); [ $rem -le 0 ] && { ok=0; break; }; [ $rem -lt $t ] && t=$rem
        tmo $t $PY runpod.py pull $id "/root/touchstone/results/v2/$d/" "$LOUT/$d/" >/dev/null 2>&1 || ok=0
      done
      rem=$(( hard - 120 - $(date +%s) )); [ $rem -gt 0 ] && tmo $(( rem < 300 ? rem : 300 )) $PY runpod.py pull $id /root/touchstone/results/logs/ logs_c_$TAG/ >/dev/null 2>&1
      if [ "$state" = "RUN OK" ] && [ $ok = 1 ]; then { verify "$LOUT/followup-churn/gate-p0" && verify "$LOUT/followup-churn/p0.01" && verify "$LOUT/followup-churn/p0.05" && verify_run "$LOUT/followup-churn/run.json" $a0 $cph $PRIORT $CAP; } || ok=0; fi
      [ $ok = 1 ] && break
      echo "$(date +%H:%M) pull or verification failed (try $try)"
      if [ "$state" = "RUN OK" ]; then [ "$(date +%s)" -ge $(( hard - 120 )) ] && break; else [ $try -ge 3 ] && break; fi
      sleep 60
    done
    [ $ok = 1 ] || { [ "$state" = "RUN OK" ] && state="RUN OK BUT RECORDS NOT VERIFIED"; rc=1; }
  fi
  if [ -n "$id" ]; then
    if $PY podctl.py delete $id 1800; then echo "$(date +%H:%M) $id deleted (verified)"; echo "$id $(date +%s) deleted" >> "$ATT"; else echo "$(date +%H:%M) $id: deletion not verified in 30 min; the watchdog keeps trying (billing may continue)"; rc=1; unresolved=1; fi
  fi
  $PY podctl.py reconcile $NAME || { echo "$(date +%H:%M) reconcile failed; the watchdog keeps trying"; rc=1; unresolved=1; }
  grep -qx pending "$P/$NAME.request" 2>/dev/null && { echo "$(date +%H:%M) a creation request is outstanding or ambiguous; the watchdog settles for 30 minutes"; unresolved=1; }
  touch "$DONE"     # the watchdog then deletes any orphan pod and exits only after its settle time of empty listings
  if [ -z "$wd" ] || ! kill -0 "$wd" 2>/dev/null; then
    echo "$(date +%H:%M) WATCHDOG NOT RUNNING"; rc=1
    if [ $req = 0 ]; then unlock; else unresolved=1; echo "$(date +%H:%M) $NAME.launchlock kept: no process deletes a late pod; check the Runpod console"; fi
  fi
  if [ "$req" = 0 ] && [ -e "$P/$NAME.bal0" ]; then   # no request was sent: nothing to record; keep the baseline as unused
    mkdir -p "$P/spend_records" && mv -- "$P/$NAME.bal0" "$P/spend_records/$NAME.$(date +%s).bal0.unused"
  fi
  [ "$tfirst" -gt 0 ] && echo "$(date +%H:%M) spend estimate so far (not a record): $(( $(date +%s) - tfirst ))s at the ceiling $MAXCPH USD/h = $($PY -c "import math; print(math.ceil(($(date +%s)-$tfirst)/3600*float('$MAXCPH')*1000)/1000)") USD (pod events in $ATT)"
  [ "$req" -gt 0 ] && echo "$(date +%H:%M) record the spend with: podctl.py spend $NAME (at least 1 h after the watchdog ends; logs_c_$TAG/watchdog.log)"
  [ -n "$unresolved" ] && { echo "$(date +%H:%M) UNRESOLVED: check the Runpod console the next day before any relaunch (plan step 4)"; rc=1; }
  echo "$(date +%H:%M) end: $state"
  exit $rc
}
trap cleanup EXIT INT TERM
# Deadlines from the first creation request at the price ceiling MAXCPH (a bound across attempts), less PRIOR: the
# soft deadline leaves CAP - PRIOR, the hard deadline HARD x CAP - PRIOR (r1 review).
t0=$(date +%s); soft=$(( t0 + $($PY -c "print(int(3600*(float('$CAP')-float('$PRIOR'))/float('$MAXCPH')))") )); hard=$(( t0 + $($PY -c "print(int(3600*(float('$CAP')*float('$HARD')-float('$PRIOR'))/float('$MAXCPH')))") ))
nohup $PY podctl.py watchdog $NAME $hard "$DONE" >> logs_c_$TAG/watchdog.log 2>&1 &
wd=$!; echo $wd > "$P/$NAME.wdpid"; disown
sleep 1; kill -0 "$wd" 2>/dev/null || { state="WATCHDOG DID NOT START"; exit 1; }
# One creation request at a time (create_one.py, no hidden retries). Before EVERY request: reconciliation must succeed (no
# untracked pod), the watchdog must allow creation, and the soft deadline must be ahead. An unambiguous refusal (HTTP 4xx,
# e.g. no capacity) tries the next flavor. An AMBIGUOUS answer ends creation for this launch (r11): no further request,
# so two pods can never overlap. NAME.request is "pending" from before each request until a clear answer (r15), so a stop
# during creation also makes the watchdog delete a late pod and settle for 30 minutes.
tries=0
while [ $tries -lt 3 ] && [ $req -lt 36 ]; do
  kill -0 "$wd" 2>/dev/null || { state="WATCHDOG NOT RUNNING BEFORE REQUEST $((req+1))"; exit 1; }
  $PY podctl.py reconcile $NAME || { state="RECONCILE FAILED BEFORE REQUEST $((req+1))"; exit 1; }
  $PY podctl.py may-create $NAME $hard || { state="CREATION BLOCKED (hard deadline)"; exit 1; }
  [ "$(date +%s)" -lt "$soft" ] || { state="SOFT DEADLINE BEFORE START"; exit 1; }
  [ "$tfirst" -gt 0 ] || tfirst=$(date +%s)
  cph=0; id=""
  { echo pending > "$P/$NAME.request" && grep -qx pending "$P/$NAME.request"; } || { state="CANNOT WRITE $NAME.request BEFORE REQUEST $((req+1))"; exit 1; }
  req=$((req+1)); rq0=$(date +%s)   # billing may start with the request (r1 review): every charge counts from here
  out=$(tmo 120 $PY create_one.py $NAME $(( (req-1) % 12 )) 2>/dev/null | tail -n 1)
  id=$(echo "$out" | $PY -c 'import sys,json; print(json.loads(sys.stdin.read()).get("id",""))' 2>/dev/null)
  amb=$(echo "$out" | $PY -c 'import sys,json; d=json.loads(sys.stdin.read() or "{}"); print(1 if d.get("ambiguous", True) else 0)' 2>/dev/null || echo 1)
  if [ -z "$id" ]; then
    if [ "$amb" = 1 ]; then echo "$(date +%H:%M) ambiguous creation answer; no further request"; state="AMBIGUOUS CREATION ANSWER (no retry)"; exit 1; fi
    echo clear > "$P/$NAME.request"; continue
  fi
  echo clear > "$P/$NAME.request"
  v=16; a0=$rq0; echo "$id $rq0 start" >> "$ATT"
  # Only a finite positive price at or below the ceiling is accepted; otherwise (above, missing, null, zero, failed
  # listing, timeout) the pod is deleted at once, with no retrieval (r15); the balance difference records what it cost.
  cph=$(tmo 60 $PY podctl.py price $id 2>/dev/null) || cph=""
  if ! $PY -c "import sys; sys.exit(0 if 0<float(sys.argv[1])<=float(sys.argv[2]) else 1)" "${cph:-0}" "$MAXCPH" 2>/dev/null; then
    state="PRICE ${cph:-unknown} NOT IN (0, $MAXCPH]"; echo "$(date +%H:%M) $id: $state; deleting"
    $PY podctl.py delete $id 600 && { echo "$id $(date +%s) deleted" >> "$ATT"; id=""; }; exit 1
  fi
  u0=$(date +%s); up=""; while [ "$(date +%s)" -lt "$soft" ] && [ $(( $(date +%s) - u0 )) -lt 240 ]; do r=$(tmo 30 $PY runpod.py ssh $id 'echo up' 2>/dev/null | head -c 2); [ "$r" = up ] && { up=1; break; }; sleep 10; done
  [ -n "$up" ] && break
  echo "$(date +%H:%M) $id unreachable; deleting"; $PY podctl.py delete $id 600 || { state="UNREACHABLE POD NOT DELETED"; exit 1; }; echo "$id $(date +%s) deleted" >> "$ATT"; id=""; tries=$((tries+1))
done
[ -z "$id" ] && { state="NO POD"; exit 1; }
echo "$(date +%H:%M) pod $id ($v vCPU, $cph USD/h): soft stop in $(( soft - $(date +%s) ))s, hard stop in $(( hard - $(date +%s) ))s (cap $CAP USD)"
tmo 900 $PY runpod.py push $id $TGZ /root/rc.tgz >/dev/null 2>&1 || { state="UPLOAD FAILED (code)"; exit 1; }
tmo 1800 $PY runpod.py push $id $BTGZ /root/rb.tgz >/dev/null 2>&1 || { state="UPLOAD FAILED (bundle)"; exit 1; }
tmo 900 $PY runpod.py ssh $id 'set -e; mkdir -p touchstone bundle; tar xzf rc.tgz -C touchstone; tar xzf rb.tgz -C bundle; which uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; }; export PATH=$HOME/.local/bin:$PATH; cd touchstone; uv sync --frozen -q; mkdir -p results/logs' >/dev/null 2>&1 || { state="PREP FAILED (unpack or sync)"; exit 1; }
chk=$(tmo 300 $PY runpod.py ssh $id "cd touchstone; export PATH=\$HOME/.local/bin:\$PATH; echo git=\$(git rev-parse HEAD 2>&1) env=\${TOUCHSTONE_IDENTITY_SALT:-unset} bundle=\$(ls /root/bundle/eval-all/freeze | wc -l); m=\$(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null); case \$m in max|''|9223372036854*) m=\$(awk '/MemTotal/ {print \$2*1024}' /proc/meminfo);; esac; echo memgb=\$((m/1073741824)); echo py=\$(uv run --frozen python -c 'import platform,numpy;print(platform.python_version(),numpy.__version__)' 2>&1 | tail -n 1 | tr ' ' _)" 2>/dev/null | tr '\n' ' ')
echo "$(date +%H:%M) prep: $chk"
case "$chk" in *"git=$EXPECT"*"env=unset"*) ;; *) state="PREP FAILED"; exit 1 ;; esac
memgb=$(echo "$chk" | sed -n 's/.*memgb=\([0-9]*\).*/\1/p'); [ -n "$memgb" ] && [ "$memgb" -ge "$MINMEM" ] || { state="PREP FAILED (memory ${memgb:-unknown} GB < $MINMEM GB)"; exit 1; }
# Charges before this pod, for the driver's cap admission: PRIOR (earlier launches, recorded) plus this launch's
# deleted attempts at the ceiling MAXCPH (an upper bound; the balance difference records the real spend).
PRIORT=$($PY - "$ATT" "$MAXCPH" "$PRIOR" <<'PYA'
import math, sys
start, tot = {}, float(sys.argv[3])
for l in open(sys.argv[1]):
    f = l.split()
    if len(f) == 3 and f[2] == "start": start[f[0]] = int(f[1])
    elif len(f) == 3 and f[2] == "deleted" and f[0] in start: tot += (int(f[1]) - start.pop(f[0])) / 3600 * float(sys.argv[2])
print(math.ceil(tot * 10000) / 10000)   # rounded up, never down (r1 review)
PYA
) || { state="PRIOR CHARGES UNKNOWN"; exit 1; }
RS=$(mktemp "/tmp/${NAME}_remote.XXXXXX") || { state="CANNOT WRITE THE REMOTE SCRIPT"; exit 1; }   # private path (r1 review)
cat > "$RS" <<EOS
#!/bin/bash
R=\${REMOTE_ROOT:-/root}   # the pod's root; the offline harness runs this script under another root with a stub driver
echo "== remote started \$(date +%H:%M)"
cd \$R/touchstone || { echo "== RUN FAILED at setup \$(date +%H:%M)"; exit 1; }; export OMP_NUM_THREADS=1 PATH=\$HOME/.local/bin:\$PATH; unset TOUCHSTONE_IDENTITY_SALT; unset TOUCHSTONE_LOCKED
B=\$R/bundle; A="--src \$B/eval-all --draw \$B/draw/draw.json --instances \$B/draw/instances.json --cfgs \$B/deviation/cfg_linux.json --addendum \$B/report/addendum.json --started $a0 --usd-per-hour $cph --prior-usd $PRIORT --stop-usd $CAP --require-identical"
D=docs/revision/churn/churn_v2.py
{ [ -e \$R/STOP ] || [ \$(date +%s) -ge $soft ]; } && { echo "== STOPPED BEFORE gate (cap) \$(date +%H:%M)"; exit 1; }
echo "== gate start \$(date +%H:%M)"
# the gate passes the same cap admission as the stages: a refusal is a stop, a failed gate is GATE FAILED only when the
# driver says so, and any other error is RUN FAILED (r1 review)
uv run --frozen python \$D --gate only --out results/v2/followup-churn \$A >> results/logs/c_gate.log 2>&1 || {
  if tail -n 5 results/logs/c_gate.log | grep -q "stopped between stages"; then echo "== STOPPED BEFORE gate (cap, driver admission) \$(date +%H:%M)"
  elif tail -n 5 results/logs/c_gate.log | grep -q "the p = 0 gate failed"; then echo "== GATE FAILED \$(date +%H:%M)"
  else echo "== RUN FAILED at gate \$(date +%H:%M)"; fi; exit 1; }
echo "== gate passed (bit-identical) \$(date +%H:%M)"
for st in inputs search freeze evaluate doubling diagnostics inventory; do
  { [ -e \$R/STOP ] || [ \$(date +%s) -ge $soft ]; } && { echo "== STOPPED BEFORE \$st (cap) \$(date +%H:%M)"; exit 1; }
  echo "== stage \$st start \$(date +%H:%M) workers search $v, evaluation at most $WEVAL"
  uv run --frozen python \$D --stage \$st --workers-search $v --workers-eval $WEVAL --out results/v2/followup-churn \$A >> results/logs/c_run.log 2>&1 || {
    if tail -n 5 results/logs/c_run.log | grep -q "stopped between stages"; then echo "== STOPPED BEFORE \$st (cap, driver admission) \$(date +%H:%M)"; else echo "== RUN FAILED at \$st \$(date +%H:%M)"; fi; exit 1; }
done
echo "== RUN OK \$(date +%H:%M)"
EOS
tmo 120 $PY runpod.py push $id "$RS" /root/r_remote.sh >/dev/null 2>&1 || { state="UPLOAD FAILED (remote script)"; exit 1; }
tmo 120 $PY runpod.py ssh $id "chmod +x /root/r_remote.sh && (nohup /root/r_remote.sh > /root/touchstone/results/logs/r_remote.log 2>&1 < /dev/null &)" >/dev/null 2>&1 || { state="REMOTE START FAILED"; exit 1; }
# the run counts as started only when the remote script's first line is in its log (r16)
for i in 1 2 3 4 5 6; do sleep 10; tmo 30 $PY runpod.py ssh $id "grep -q 'remote started' /root/touchstone/results/logs/r_remote.log" >/dev/null 2>&1 && { started=1; break; }; done
[ -n "$started" ] || { state="REMOTE START FAILED (no start line)"; exit 1; }
state="RUNNING"; stopped=""
while true; do
  sleep 120
  now=$(date +%s)
  [ "$now" -ge "$hard" ] && { state="HARD DEADLINE ($HARD x cap at $MAXCPH USD/h; the watchdog deletes the pod)"; exit 1; }
  if [ "$now" -ge "$soft" ] && [ -z "$stopped" ]; then tmo 60 $PY runpod.py ssh $id 'touch /root/STOP && test -e /root/STOP' >/dev/null 2>&1 && stopped=1 && echo "$(date +%H:%M) cap reached: the pod stops after the running stage"; fi
  st=$(tmo 90 $PY runpod.py ssh $id "tail -c 240 /root/touchstone/results/logs/r_remote.log" 2>/dev/null | tr '\n' ' ')
  echo "$(date +%H:%M) [soft $(( soft - now ))s, hard $(( hard - now ))s] $st" | tail -c 320
  case "$st" in
    *"RUN OK"*) state="RUN OK"; rc=0; exit 0 ;;
    *"GATE FAILED"*) state="GATE FAILED (the driver reports the p = 0 gate failed: not passing or not bit-identical; churn cells not started)"; exit 1 ;;
    *"RUN FAILED"*|*"STOPPED BEFORE"*) state="$(echo "$st" | grep -o '== [A-Z].*' | head -c 120 | sed "s/[[:space:]]*\$//")"; exit 1 ;;
  esac
done
