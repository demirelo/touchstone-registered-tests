#!/bin/bash
# Snapshot guard: run a private copy, so an edit to this file cannot reach a running launch.
if [ -z "${LAUNCH_SNAPSHOT:-}" ]; then
  snapf="/Users/oemer.demirel/Projects/touchstone/results/pods/snap_$(basename "$0" .sh)_$$.sh"; cp "$0" "$snapf"
  LAUNCH_SNAPSHOT="$snapf" exec bash "$snapf" "$@"
fi
# Honest-churn arm (docs/revision/churn/churn-plan.md, draft 4) on one Runpod CPU pod: a copy of reset_pod.sh (podctl.py
# safety unchanged). Order on the pod: the p = 0 gate through the churn path (bit identity, --require-identical; the
# author's decision), then the 36 churn cells stage by stage for both rates (search with all vCPUs; evaluate, doubling and
# diagnostics with the workers the driver's memory preflight chooses, at most WEVAL), then the inventory. Spending (the
# author: do not kill jobs): the driver refuses a stage that would pass the cap (allocation time, price and earlier
# attempts' charges passed from this launcher), and at the soft deadline the pod stops BETWEEN stages (a STOP file read
# before each stage). The one exception: the watchdog deletes the pod at HARD x the cap at the price ceiling MAXCPH, also
# mid-stage, as an absolute guard. An EXIT/INT/TERM trap pulls what exists, deletes the pod and verifies the deletion.
# Prior attempts persist in $NAME.attempts across launches; their charges count toward the cap.
# Usage: churn_pod.sh <code_tgz> <bundle_tgz> <tag> <cap_usd> <local_out>
# Env: EXPECT (commit inside the code tarball), MAXCPH, optional WEVAL (default 10), MINMEM (default 28), HARD (default 1.3).
set -u
PY=/opt/homebrew/bin/python3; P=/Users/oemer.demirel/Projects/touchstone/results/pods
TGZ=${1:?code tarball}; BTGZ=${2:?bundle tarball}; TAG=${3:?tag}; CAP=${4:?cap_usd}; LOUT=${5:?local_out}; cd $P
EXPECT=${EXPECT:?commit}; MAXCPH=${MAXCPH:?max usd per hour}; WEVAL=${WEVAL:-9}; MINMEM=${MINMEM:-28}; HARD=${HARD:-1.3}
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
tmo() { perl -e 'alarm shift; exec @ARGV' "$@"; }
NAME=ts-c-$TAG; DONE=$P/$NAME.done; ATT=$P/$NAME.attempts
rm_ok() { [ -e "$1" ] && mv -- "$1" ~/.Trash/"$(basename "$1").$$"; true; }
rm_ok "$DONE"; rm_ok "$P/$NAME.blocked"; touch "$ATT"     # attempts persist across launches (charges of earlier attempts count)
# Charges of earlier attempts: at the recorded prices (passed to the driver) and bounded at the ceiling (for the deadlines).
prior() { $PY - "$ATT" "$MAXCPH" "$1" <<'PYP'
import sys
rows = [l.split() for l in open(sys.argv[1]) if l.strip()]
col = 3 if sys.argv[3] == "recorded" else None
print(round(sum((int(e) - int(s)) / 3600 * (float(p) if col else float(sys.argv[2])) for _, s, e, p in rows), 6))
PYP
}
id=""; state="NOT STARTED"; rc=1; cph=0; a0=0
# Pod safety lives in podctl.py (test_podctl.py, with mutation checks): fail-closed listing, deletion verified within
# elapsed time, reconciliation, a creation block from the hard deadline, and a watchdog that runs on after this launcher
# exits, until no pod named $NAME remains.
attempt_end() { [ "$a0" -gt 0 ] && echo "${id:-none} $a0 $(date +%s) ${cph:-$MAXCPH}" >> "$ATT"; a0=0; true; }
cleanup() {
  trap - EXIT INT TERM
  if [ -n "$id" ]; then
    try=0
    while :; do   # after RUN OK: keep the pod and retry until both directories verify, or until 2 min before the hard deadline
      try=$((try+1)); ok=1
      for spec in "followup-churn/ $LOUT/followup-churn/ 1800"; do
        set -- $spec; rem=$(( hard - 120 - $(date +%s) )); [ $rem -le 0 ] && { ok=0; break; }; t=$3; [ $rem -lt $t ] && t=$rem
        tmo $t $PY runpod.py pull $id /root/touchstone/results/v2/$1 "$2" >/dev/null 2>&1 || ok=0
      done
      rem=$(( hard - 120 - $(date +%s) )); [ $rem -gt 0 ] && tmo $(( rem < 300 ? rem : 300 )) $PY runpod.py pull $id /root/touchstone/results/logs/ logs_c_$TAG/ >/dev/null 2>&1
      if [ "$state" = "RUN OK" ] && [ $ok = 1 ]; then { verify "$LOUT/followup-churn/gate-p0" && verify "$LOUT/followup-churn/p0.01" && verify "$LOUT/followup-churn/p0.05"; } || ok=0; fi
      [ $ok = 1 ] && break
      echo "$(date +%H:%M) pull or verification failed (try $try)"
      if [ "$state" = "RUN OK" ]; then [ "$(date +%s)" -ge $(( hard - 120 )) ] && break; else [ $try -ge 3 ] && break; fi
      sleep 60
    done
    [ $ok = 1 ] || { [ "$state" = "RUN OK" ] && state="RUN OK BUT RECORDS NOT VERIFIED"; rc=1; }
    if $PY podctl.py delete $id 1800; then echo "$(date +%H:%M) $id deleted (verified)"; else echo "$(date +%H:%M) $id: deletion not verified in 30 min; the watchdog keeps trying"; rc=1; fi
    attempt_end
  fi
  $PY podctl.py reconcile $NAME || { echo "$(date +%H:%M) reconcile failed; the watchdog keeps trying"; rc=1; }
  touch "$DONE"     # the watchdog exits once a listing shows no pod named $NAME; after the hard deadline it keeps deleting
  $PY - "$ATT" "$MAXCPH" <<'PYS'
import sys
rows = [l.split() for l in open(sys.argv[1]) if l.strip()]
tot = sum((int(e) - int(s)) / 3600 * float(p) for _, s, e, p in rows); bound = sum((int(e) - int(s)) / 3600 * float(sys.argv[2]) for _, s, e, p in rows)
print(f"spend by attempt ({len(rows)}): {tot:.3f} USD at the recorded prices; bound {bound:.3f} USD at the ceiling (record with budget_v2.py --record)")
PYS
  echo "$(date +%H:%M) end: $state"
  exit $rc
}
trap cleanup EXIT INT TERM
# Deadlines from the first creation request at the price ceiling MAXCPH, net of earlier attempts' charges at the ceiling.
PB=$(prior bound); t0=$(date +%s)
soft=$(( t0 + $($PY -c "print(max(0,int(3600*(float('$CAP')-float('$PB'))/float('$MAXCPH'))))") )); hard=$(( t0 + $($PY -c "print(max(0,int(3600*(float('$CAP')*float('$HARD')-float('$PB'))/float('$MAXCPH'))))") ))
nohup $PY podctl.py watchdog $NAME $hard "$DONE" >> logs_c_$TAG/watchdog.log 2>&1 &
disown
for attempt in 1 2 3; do
  $PY podctl.py reconcile $NAME || { state="RECONCILE FAILED BEFORE ATTEMPT $attempt"; exit 1; }
  $PY podctl.py may-create $NAME $hard || { state="CREATION BLOCKED (hard deadline)"; exit 1; }
  [ "$(date +%s)" -lt "$soft" ] || { state="SOFT DEADLINE BEFORE START"; exit 1; }
  a0=$(date +%s); cph=$MAXCPH
  out=$(tmo 120 $PY create16.py $NAME 2>/dev/null | tail -n 1); id=$(echo "$out" | $PY -c 'import sys,json; print(json.loads(sys.stdin.read()).get("id",""))' 2>/dev/null); v=$(echo "$out" | $PY -c 'import sys,json; print(json.loads(sys.stdin.read()).get("vcpu",""))' 2>/dev/null)
  if [ -z "$id" ]; then echo "$(date +%H:%M) no capacity or lost response"; attempt_end; sleep 30; continue; fi
  cph=$(tmo 60 $PY runpod.py list 2>/dev/null | $PY -c "import sys,json; print(next((p.get('costPerHr') or 0) for p in json.load(sys.stdin) if p['id']=='$id'))" 2>/dev/null)
  $PY -c "import sys; sys.exit(0 if 0<float('${cph:-0}' or 0)<=float('$MAXCPH') else 1)" || { state="PRICE ${cph:-unknown} NOT IN (0, $MAXCPH]"; exit 1; }
  up=""; while [ "$(date +%s)" -lt "$soft" ] && [ $(( $(date +%s) - a0 )) -lt 240 ]; do r=$(tmo 30 $PY runpod.py ssh $id 'echo up' 2>/dev/null | head -c 2); [ "$r" = up ] && { up=1; break; }; sleep 10; done
  [ -n "$up" ] && break
  echo "$(date +%H:%M) $id unreachable; deleting"; $PY podctl.py delete $id 600 || { state="UNREACHABLE POD NOT DELETED"; exit 1; }; attempt_end; id=""
done
[ -z "$id" ] && { state="NO POD"; exit 1; }
PRIOR=$(prior recorded)    # earlier attempts at their recorded prices; this attempt starts at $a0 at $cph USD/h
echo "$(date +%H:%M) pod $id ($v vCPU, $cph USD/h, earlier attempts $PRIOR USD): soft stop in $(( soft - $(date +%s) ))s, hard stop in $(( hard - $(date +%s) ))s (cap $CAP USD)"
tmo 900 $PY runpod.py push $id $TGZ /root/rc.tgz >/dev/null 2>&1
tmo 1800 $PY runpod.py push $id $BTGZ /root/rb.tgz >/dev/null 2>&1
tmo 900 $PY runpod.py ssh $id 'mkdir -p touchstone bundle && tar xzf rc.tgz -C touchstone && tar xzf rb.tgz -C bundle && (which uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh 2>/dev/null | sh >/dev/null 2>&1); export PATH=$HOME/.local/bin:$PATH; cd touchstone && uv sync --frozen -q 2>&1 | tail -n 2; mkdir -p results/logs' >/dev/null 2>&1
chk=$(tmo 300 $PY runpod.py ssh $id "cd touchstone; export PATH=\$HOME/.local/bin:\$PATH; echo git=\$(git rev-parse HEAD 2>&1) env=\${TOUCHSTONE_IDENTITY_SALT:-unset} bundle=\$(ls /root/bundle/eval-all/freeze | wc -l); m=\$(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null); case \$m in max|''|9223372036854*) m=\$(awk '/MemTotal/ {print \$2*1024}' /proc/meminfo);; esac; echo memgb=\$((m/1073741824)); echo py=\$(uv run --frozen python -c 'import platform,numpy;print(platform.python_version(),numpy.__version__)' 2>&1 | tail -n 1 | tr ' ' _)" 2>/dev/null | tr '\n' ' ')
echo "$(date +%H:%M) prep: $chk"
case "$chk" in *"git=$EXPECT"*"env=unset"*) ;; *) state="PREP FAILED"; exit 1 ;; esac
memgb=$(echo "$chk" | sed -n 's/.*memgb=\([0-9]*\).*/\1/p'); [ -n "$memgb" ] && [ "$memgb" -ge "$MINMEM" ] || { state="PREP FAILED (memory ${memgb:-unknown} GB < $MINMEM GB)"; exit 1; }
cat > /tmp/c_remote_$TAG.sh <<EOS
#!/bin/bash
cd /root/touchstone; export OMP_NUM_THREADS=1 PATH=\$HOME/.local/bin:\$PATH; unset TOUCHSTONE_IDENTITY_SALT; unset TOUCHSTONE_LOCKED
B=/root/bundle; A="--src \$B/eval-all --draw \$B/draw/draw.json --instances \$B/draw/instances.json --cfgs \$B/deviation/cfg_linux.json --addendum \$B/report/addendum.json --started $a0 --usd-per-hour $cph --prior-usd $PRIOR --stop-usd $CAP --require-identical"
D=docs/revision/churn/churn_v2.py
{ [ -e /root/STOP ] || [ \$(date +%s) -ge $soft ]; } && { echo "== STOPPED BEFORE gate (cap) \$(date +%H:%M)"; exit 1; }
echo "== gate start \$(date +%H:%M)"
uv run --frozen python \$D --gate only --out results/v2/followup-churn \$A >> results/logs/c_gate.log 2>&1 || { echo "== GATE FAILED \$(date +%H:%M)"; exit 1; }
echo "== gate passed (bit-identical) \$(date +%H:%M)"
for st in inputs search freeze evaluate doubling diagnostics inventory; do
  { [ -e /root/STOP ] || [ \$(date +%s) -ge $soft ]; } && { echo "== STOPPED BEFORE \$st (cap) \$(date +%H:%M)"; exit 1; }
  echo "== stage \$st start \$(date +%H:%M)"
  uv run --frozen python \$D --stage \$st --workers-search $v --workers-eval $WEVAL --out results/v2/followup-churn \$A >> results/logs/c_run.log 2>&1 || { echo "== RUN FAILED at \$st \$(date +%H:%M)"; exit 1; }
done
echo "== RUN OK \$(date +%H:%M)"
EOS
tmo 120 $PY runpod.py push $id /tmp/c_remote_$TAG.sh /root/c_remote.sh >/dev/null 2>&1
tmo 120 $PY runpod.py ssh $id "chmod +x /root/c_remote.sh; (nohup /root/c_remote.sh > /root/touchstone/results/logs/c_remote.log 2>&1 < /dev/null &)" >/dev/null 2>&1
state="RUNNING"; stopped=""
while true; do
  sleep 120
  now=$(date +%s)
  [ "$now" -ge "$hard" ] && { state="HARD DEADLINE ($HARD x cap at $MAXCPH USD/h; the watchdog deletes the pod)"; exit 1; }
  if [ "$now" -ge "$soft" ] && [ -z "$stopped" ]; then tmo 60 $PY runpod.py ssh $id 'touch /root/STOP && test -e /root/STOP' >/dev/null 2>&1 && stopped=1 && echo "$(date +%H:%M) cap reached: the pod stops after the running stage"; fi
  st=$(tmo 90 $PY runpod.py ssh $id "tail -c 240 /root/touchstone/results/logs/c_remote.log" 2>/dev/null | tr '\n' ' ')
  echo "$(date +%H:%M) [soft $(( soft - now ))s, hard $(( hard - now ))s] $st" | tail -c 320
  case "$st" in
    *"RUN OK"*) state="RUN OK"; rc=0; exit 0 ;;
    *"GATE FAILED"*) state="GATE FAILED (not bit-identical; 36 cells not started)"; exit 1 ;;
    *"RUN FAILED"*|*"STOPPED BEFORE"*) state="$(echo "$st" | grep -o '== [A-Z].*' | head -c 120)"; exit 1 ;;
  esac
done
