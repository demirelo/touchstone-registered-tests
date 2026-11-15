#!/bin/bash
# Snapshot guard: run a private copy, so an edit to this file cannot reach a running launch.
if [ -z "${LAUNCH_SNAPSHOT:-}" ]; then
  snapf="/Users/oemer.demirel/Projects/touchstone/results/pods/snap_$(basename "$0" .sh)_$$.sh"; cp "$0" "$snapf"
  LAUNCH_SNAPSHOT="$snapf" exec bash "$snapf" "$@"
fi
# Follow-up Runs A (runner-up comparator, docs/revision/followup2/runner-up-plan.md, draft 7) and B (continued searches,
# convergence-plan.md, draft 7) on one Runpod CPU pod each. Generated from churn_pod.sh (itself from the reviewed
# reset_pod.sh, rounds r9-r18, and churn launcher reviews r1-r2): pod safety, launch lock, price ceiling, watchdog, spend
# records, request-time attempts and deadlines net of PRIOR are unchanged. What differs (launcher-notes.md):
# - The first argument selects the run (A or B): its name, ledger run tag, plan cap, remote steps and output directories.
# - NAME is per run (ts-f2a, ts-f2b), not per launch tag (review r1): one launch lock, balance baseline and spend record
#   per run, so two launches of a run never overlap and a launch is refused while the previous one's spend is unrecorded.
#   The launch tag names this launch's reservation (<run tag>-<tag>, category followup); any other open reservation of
#   the run (an unrecorded earlier launch) refuses the launch. One validated ledger snapshot gives PRIOR and is pushed.
# - PRIOR is not an operator input: it is the spend the ledger records for this run's tag (the same rule as the drivers'
#   guards.ledger_spend), and a reservation for the run tag must cover the watchdog bound HARD x CAP - PRIOR.
# - Before every paid step on the pod (the reproduction gate included) the remote script checks the STOP file and the soft
#   deadline, then runs guards.py admit with the plan's cap, the ceiling MAXCPH, the live pod's request time, this
#   launch's attempts file and the ledger (both pushed to the pod before the remote script starts; neither can change
#   while the pod runs), the run tag and the step's estimate; the step starts only on exit 0.
# - Run A: the reset driver's reproduction gate (--reproduce --require-identical, bit-identical), then runnerup_v2.py
#   --stage all. Run B: convergence_v2.py --gate --site pod on the two gate cells, then the main run with the four gate
#   records (two Mac records from the bundle, two from this pod). Run B is refused before any marker unless both Mac gate
#   records in the bundle pass and bind to EXPECT (their binding includes the commit).
# - After RUN OK every output directory is verified: each inventoried record exists with its hash, and every file in the
#   directory (except inventory.json, *.lock, *.tmp) is inventoried.
# Spending (the author: do not kill jobs): at the cap the pod stops BETWEEN steps; only at HARD x the cap is the pod deleted
# mid-step (the watchdog). An EXIT/INT/TERM trap pulls what exists (only if the run started), deletes the pod and verifies
# it. Spend (r16): the record is the account balance difference (podctl.py spend NAME, at least an hour after the watchdog
# ends); this launcher prints only estimates. One launch per NAME at a time (NAME.launchlock; the watchdog releases it).
# Usage: followup2_pod.sh <A|B> <code_tgz> <bundle_tgz> <tag> <cap_usd> <local_out>   (no spaces in paths)
# Env: EXPECT (commit inside the code tarball), MAXCPH, optional MINMEM (default 28), HARD (default 1.3), LEDGER (default
# the worktree's docs/revision/budget-ledger.json).
set -u
PY=/opt/homebrew/bin/python3; P=/Users/oemer.demirel/Projects/touchstone/results/pods
RUN=${1:?run A or B}; TGZ=${2:?code tarball}; BTGZ=${3:?bundle tarball}; TAG=${4:?tag}; CAP=${5:?cap_usd}; LOUT=${6:?local_out}; cd $P
case "$TGZ$BTGZ$TAG$LOUT" in *[[:space:]]*) echo "refused: a path or tag contains whitespace"; exit 1 ;; esac
case "$RUN" in
  A) NAME=ts-f2a; RUNTAG=runner-up; PLANCAP=3.00; OUTS="followup2-a-pod-gate followup2-runnerup" ;;
  B) NAME=ts-f2b; RUNTAG=convergence2; PLANCAP=5.00; OUTS="followup2-conv" ;;   # the rerun: its own tag and cap (plan, rerun amendment)
  *) echo "refused: the run must be A or B"; exit 1 ;;
esac
EXPECT=${EXPECT:?commit}; MAXCPH=${MAXCPH:?max usd per hour}; MINMEM=${MINMEM:-28}; HARD=${HARD:-1.3}
# Run B worker count (Run B rerun): one killed worker lost the first Run B; the count comes from the Mac-measured peak memory
# per cell (convergence-plan.md, rerun section); a lost worker restarts the stage once at half the count (saved cells skipped).
CONVWORKERS=${CONVWORKERS:-7}   # 7 x 2.39 GB (Mac peak, X7-SC cell) = 16.7 GB of 28: margin 1.6
case "$CONVWORKERS" in [1-9]|1[0-6]) ;; *) echo "refused: CONVWORKERS must be an integer from 1 to 16"; exit 1 ;; esac
CONVRETRY=$(( CONVWORKERS > 1 ? CONVWORKERS / 2 : 1 ))
LEDGER=${LEDGER:-/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79/docs/revision/budget-ledger.json}
[ -z "${PRIOR+x}" ] || { echo "refused: PRIOR is not an input here; it is the ledger's recorded spend for the run tag $RUNTAG"; exit 1; }
$PY -c "import math,sys; c=float(sys.argv[1]); p=float(sys.argv[2]); sys.exit(0 if math.isfinite(c) and 0 < c <= p else 1)" "$CAP" "$PLANCAP" 2>/dev/null || { echo "refused: the cap must be positive and at most the plan's $PLANCAP USD"; exit 1; }
LOGD=logs_f2$(echo $RUN | tr AB ab)_$TAG; mkdir -p "$LOUT" $LOGD
$PY -c "import sys,tarfile; ms=tarfile.open(sys.argv[1]).getmembers(); d=[m.name for m in ms if m.name.split('/')[-1].startswith('._')]; o=[m.name for m in ms if m.uid!=0]; print('tarball guard: %d AppleDouble, %d non-root' % (len(d),len(o))); sys.exit(1 if d or o else 0)" "$TGZ" || { echo "code tarball refused"; exit 1; }
# Bundle guard: the evidence the run needs is present and passing; Run B's Mac gate records bind to EXPECT.
$PY - "$BTGZ" "$RUN" "$EXPECT" <<'PYB' || { echo "bundle refused"; exit 1; }
import json, sys, tarfile
t = tarfile.open(sys.argv[1]); run, exp = sys.argv[2], sys.argv[3]
names = {m.name.lstrip("./"): m for m in t.getmembers() if m.isfile()}
def rec(n):
    m = names.get(n)
    return json.load(t.extractfile(m)) if m is not None else None
if run == "A":
    need = {"evidence/a-gate-repro/gate.json": "reproduction gate", "evidence/a-gate-dbl/gate.json": "doubling gate"}
    bad = [n for n, s in need.items() if not ((rec(n) or {}).get("pass") is True and (rec(n) or {}).get("stage") == s)]
else:
    need = ["evidence/conv-gate-mac/headline@rho0.2__F111__X7-SC__profit__mac.json", "evidence/conv-gate-mac/fresh1@rho0.2__F111__D2+H3__profit__mac.json"]
    bad = [n for n in need if not ((rec(n) or {}).get("pass") is True and (rec(n) or {}).get("site") == "mac"
                                   and ((rec(n) or {}).get("binding") or {}).get("provenance", {}).get("git_commit") == exp)]
print(f"bundle guard: run {run}, {len(need) - len(bad)} of {len(need)} evidence records pass" + (f"; refused: {bad} (missing, failed, or not bound to {exp})" if bad else ""))
sys.exit(1 if bad else 0)
PYB
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
( guard "$hg" ); g=$?; mv -- "$hg" ~/.Trash/hg_f2_$$
[ $g -eq 0 ] || { echo "code tarball refused"; exit 1; }
# verify DIR: every record in DIR/inventory.json exists with its hash, and every file in DIR (except inventory.json and
# *.lock, *.tmp, which the drivers' inventories also leave out) is in the inventory: nothing outside it goes unchecked.
verify() { $PY - "$1" <<'PYV'
import hashlib, json, sys
from pathlib import Path
d = Path(sys.argv[1])
try:
    recs = json.loads((d / "inventory.json").read_text())["records"]
except Exception:
    print(f"verify {d.name}: no readable inventory"); sys.exit(1)
bad = [k for k, h in recs.items() if not (d / k).is_file() or hashlib.sha256((d / k).read_bytes()).hexdigest() != h]
extra = [str(p.relative_to(d)) for p in d.rglob("*") if p.is_file() and p.name != "inventory.json" and not p.name.endswith((".lock", ".tmp"))
         and str(p.relative_to(d)) not in recs]
print(f"verify {d.name}: {len(recs)} records, {len(bad)} bad, {len(extra)} not inventoried"); sys.exit(1 if bad or extra or not recs else 0)
PYV
}
tmo() { perl -e 'alarm shift; exec @ARGV' "$@"; }
DONE=$P/$NAME.done; ATT=$P/$NAME.attempts
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
# The ledger is read only under the run lock (review r2, Sol 1): a second launch delayed before the lock validates
# against the ledger as it is when it holds the lock (the first launch's recorded spend, its consumed reservation).
# PRIOR from the ledger (guards.ledger_spend's rule: a `spent` list of rows with a tag and a finite, nonnegative amount;
# rows whose tag starts with the run tag count); it must lie below the cap, and a reservation for the run tag must cover
# the watchdog bound HARD x CAP - PRIOR (churn launcher review r1: the reservation is the bound, not the stop cap).
# One snapshot of the ledger (review r1, Astra 2): it is validated here, gives PRIOR for the deadlines, and is the copy
# pushed to the pod for every admission; a later change to the ledger file cannot reach this launch.
SNAP=$(mktemp "/tmp/${NAME}_ledger.XXXXXX") && cp "$LEDGER" "$SNAP" 2>/dev/null || { echo "refused: cannot snapshot the ledger $LEDGER"; unlock; exit 1; }
PRIOR=$($PY - "$SNAP" "$RUNTAG" "$CAP" "$HARD" "$TAG" <<'PYL'
import json, math, sys
led, tag, cap, hard, launch = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
def num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0
try:
    d = json.load(open(led))
except Exception:
    print("refused: no readable budget ledger at " + led); sys.exit(1)
if not isinstance(d, dict) or not isinstance(d.get("spent"), list) or not isinstance(d.get("reservations", []), list):
    print("refused: the ledger needs a `spent` list"); sys.exit(1)
tot = 0.0
for r in d["spent"]:
    if not isinstance(r, dict) or "tag" not in r or not num(r.get("usd")):
        print(f"refused: a malformed spend row in the ledger: {r!r}"); sys.exit(1)
    if str(r["tag"]).startswith(tag): tot += float(r["usd"])
if not tot < cap:
    print(f"refused: the ledger records {tot:.4f} USD for {tag}, not below the cap {cap}"); sys.exit(1)
need = hard * cap - tot
# This launch's reservation is the one tagged <run tag>-<launch tag> in category followup (review r1, Astra 1); any other
# open reservation of the run is an earlier launch whose spend is not recorded yet (recording replaces the reservation),
# so PRIOR would miss it: refused, as churn refuses an unrecorded previous launch.
mine = [r for r in d.get("reservations", []) if isinstance(r, dict) and r.get("tag") == f"{tag}-{launch}"]
other = [r.get("tag") for r in d.get("reservations", []) if isinstance(r, dict) and str(r.get("tag", "")).startswith(tag + "-") and r.get("tag") != f"{tag}-{launch}"]
if other:
    print(f"refused: open reservations {other} of {tag}: an earlier launch's spend is not recorded in the ledger"); sys.exit(1)
if any(str(r.get("tag")) == f"{tag}-{launch}" for r in d["spent"]):
    print(f"refused: {tag}-{launch} already has a spend record; use a new launch tag"); sys.exit(1)
if len(mine) != 1 or mine[0].get("op") != "followup" or not num(mine[0].get("cap")) or float(mine[0]["cap"]) < need - 1e-6:
    print(f"refused: no single followup reservation {tag}-{launch} covers the watchdog bound {need:.4f} USD (HARD x CAP - PRIOR)"); sys.exit(1)
print(round(tot, 6))
PYL
) || { echo "$PRIOR"; unlock; exit 1; }
echo "ledger: PRIOR $PRIOR USD recorded for $RUNTAG; reservation $RUNTAG-$TAG covers the watchdog bound (snapshot $SNAP)"
[ -n "${DRYRUN:-}" ] && { echo "dry run: guards passed; no pod created"; unlock; exit 0; }
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
    while :; do   # after RUN OK: keep the pod and retry until every directory verifies, or until 2 min before the hard deadline
      try=$((try+1)); ok=1
      for d in $OUTS; do
        t=1800
        rem=$(( hard - 120 - $(date +%s) )); [ $rem -le 0 ] && { ok=0; break; }; [ $rem -lt $t ] && t=$rem
        tmo $t $PY runpod.py pull $id "/root/touchstone/results/v2/$d/" "$LOUT/$d/" >/dev/null 2>&1 || ok=0
      done
      rem=$(( hard - 120 - $(date +%s) )); [ $rem -gt 0 ] && tmo $(( rem < 300 ? rem : 300 )) $PY runpod.py pull $id /root/touchstone/results/logs/ $LOGD/ >/dev/null 2>&1
      pulled=$ok   # verify on every end state (lessons.md: Run A's records went unverified after STOPPED); retry only after RUN OK
      if [ $pulled = 1 ]; then for d in $OUTS; do verify "$LOUT/$d" || ok=0; done; fi
      [ $ok = 1 ] && break
      [ "$state" != "RUN OK" ] && [ $pulled = 1 ] && { echo "$(date +%H:%M) end state $state: pulled records do not all verify (see above)"; break; }
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
  [ "$req" -gt 0 ] && echo "$(date +%H:%M) record the spend with: podctl.py spend $NAME (at least 1 h after the watchdog ends; $LOGD/watchdog.log), then budget_v2.py --record with a tag starting $RUNTAG-"
  [ -n "$unresolved" ] && { echo "$(date +%H:%M) UNRESOLVED: check the Runpod console the next day before any relaunch"; rc=1; }
  echo "$(date +%H:%M) end: $state"
  exit $rc
}
trap cleanup EXIT INT TERM
# Deadlines from the first creation request at the price ceiling MAXCPH (a bound across attempts), less PRIOR: the
# soft deadline leaves CAP - PRIOR, the hard deadline HARD x CAP - PRIOR (churn r1 review).
t0=$(date +%s); soft=$(( t0 + $($PY -c "print(int(3600*(float('$CAP')-float('$PRIOR'))/float('$MAXCPH')))") )); hard=$(( t0 + $($PY -c "print(int(3600*(float('$CAP')*float('$HARD')-float('$PRIOR'))/float('$MAXCPH')))") ))
nohup $PY podctl.py watchdog $NAME $hard "$DONE" >> $LOGD/watchdog.log 2>&1 &
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
  req=$((req+1)); rq0=$(date +%s)   # billing may start with the request (churn r1 review): every charge counts from here
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
echo "$(date +%H:%M) pod $id ($v vCPU, $cph USD/h): soft stop in $(( soft - $(date +%s) ))s, hard stop in $(( hard - $(date +%s) ))s (run $RUN, cap $CAP USD, PRIOR $PRIOR USD)"
tmo 900 $PY runpod.py push $id $TGZ /root/rc.tgz >/dev/null 2>&1 || { state="UPLOAD FAILED (code)"; exit 1; }
tmo 1800 $PY runpod.py push $id $BTGZ /root/rb.tgz >/dev/null 2>&1 || { state="UPLOAD FAILED (bundle)"; exit 1; }
tmo 900 $PY runpod.py ssh $id 'set -e; mkdir -p touchstone bundle; tar xzf rc.tgz -C touchstone; tar xzf rb.tgz -C bundle; which uv >/dev/null || { curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; }; export PATH=$HOME/.local/bin:$PATH; cd touchstone; uv sync --frozen -q; mkdir -p results/logs' >/dev/null 2>&1 || { state="PREP FAILED (unpack or sync)"; exit 1; }
chk=$(tmo 300 $PY runpod.py ssh $id "cd touchstone; export PATH=\$HOME/.local/bin:\$PATH; echo git=\$(git rev-parse HEAD 2>&1) env=\${TOUCHSTONE_IDENTITY_SALT:-unset} bundle=\$(ls /root/bundle/eval-all/freeze | wc -l); m=\$(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null); case \$m in max|''|9223372036854*) m=\$(awk '/MemTotal/ {print \$2*1024}' /proc/meminfo);; esac; echo memgb=\$((m/1073741824)); echo py=\$(uv run --frozen python -c 'import platform,numpy;print(platform.python_version(),numpy.__version__)' 2>&1 | tail -n 1 | tr ' ' _)" 2>/dev/null | tr '\n' ' ')
echo "$(date +%H:%M) prep: $chk"
case "$chk" in *"git=$EXPECT"*"env=unset"*) ;; *) state="PREP FAILED"; exit 1 ;; esac
memgb=$(echo "$chk" | sed -n 's/.*memgb=\([0-9]*\).*/\1/p'); [ -n "$memgb" ] && [ "$memgb" -ge "$MINMEM" ] || { state="PREP FAILED (memory ${memgb:-unknown} GB < $MINMEM GB)"; exit 1; }
# The admission inputs (plans section 5, launcher handoff): this launch's attempts file (closed attempts count at the
# ceiling; the open start is this pod's request time) and the ledger (earlier launches of the run tag). Both are fixed
# for the pod's life (no attempt event or ledger row can appear while it runs), so one push covers every paid step.
tmo 120 $PY runpod.py push $id "$ATT" /root/f2.attempts >/dev/null 2>&1 || { state="UPLOAD FAILED (attempts)"; exit 1; }
tmo 120 $PY runpod.py push $id "$SNAP" /root/f2.ledger.json >/dev/null 2>&1 || { state="UPLOAD FAILED (ledger)"; exit 1; }
# The run's own steps, kept literal ($ expands on the pod); inserted into the remote script below as one value.
if [ "$RUN" = A ]; then
RBODY=$(cat <<'RA'
step "reset gate" 0.61
uv run --frozen python docs/revision/followup/reset_followup_v2.py --reproduce --require-identical --out results/v2/followup2-a-pod-gate $IN >> $L/f2_gate.log 2>&1 || {
  if tail -n 5 $L/f2_gate.log | grep -q '"gate_ok": false'; then echo "== GATE FAILED at reset gate (not bit-identical) $(date +%H:%M)"; else echo "== RUN FAILED at reset gate $(date +%H:%M)"; fi; exit 1; }
echo "== reset gate passed (bit-identical) $(date +%H:%M)"
step "runner-up" 2.65
uv run --frozen python docs/revision/followup2/runnerup_v2.py --stage all --workers 12 --site pod --out results/v2/followup2-runnerup $IN --reset-mac $B/evidence/a-gate-repro --reset-pod results/v2/followup2-a-pod-gate --doubling-evidence $B/evidence/a-gate-dbl $PAID >> $L/f2_run.log 2>&1; drc=$?
if [ $drc = 3 ]; then s=$(tail -n 5 $L/f2_run.log | grep -o '"stopped_before": "[a-z]*"' | tail -n 1 | cut -d'"' -f4); echo "== STOPPED BEFORE ${s:-runner-up} (cap, driver admission) $(date +%H:%M)"; exit 1; fi
[ $drc = 0 ] || { echo "== RUN FAILED at runner-up $(date +%H:%M)"; exit 1; }
RA
)
else
RBODY=$(cat <<'RB'
O=results/v2/followup2-conv; GC="headline@rho0.2|F111|X7-SC|profit,fresh1@rho0.2|F111|D2+H3|profit"
step "convergence gate" 1.06
uv run --frozen python docs/revision/followup2/convergence_v2.py --gate --site pod --cells "$GC" --out $O $IN $PAID >> $L/f2_gate.log 2>&1; drc=$?
if [ $drc = 3 ]; then echo "== STOPPED BEFORE convergence gate (cap, driver admission) $(date +%H:%M)"; exit 1
elif [ $drc = 4 ]; then echo "== GATE FAILED at convergence gate (round 1 differs from the registered record) $(date +%H:%M)"; exit 1
elif [ $drc != 0 ]; then echo "== RUN FAILED at convergence gate $(date +%H:%M)"; exit 1; fi
echo "== convergence gate passed $(date +%H:%M)"
EV="--evidence $B/evidence/conv-gate-mac/headline@rho0.2__F111__X7-SC__profit__mac.json --evidence $B/evidence/conv-gate-mac/fresh1@rho0.2__F111__D2+H3__profit__mac.json --evidence $O/gate/headline@rho0.2__F111__X7-SC__profit__pod.json --evidence $O/gate/fresh1@rho0.2__F111__D2+H3__profit__pod.json"
step "convergence" 5.10
uv run --frozen python docs/revision/followup2/convergence_v2.py --workers @CW@ --site pod --out $O $IN $EV $PAID >> $L/f2_run.log 2>&1; drc=$?
if [ $drc = 5 ]; then                  # a lost worker: the finished cells are saved; one restart at half the workers runs the rest
  echo "== convergence lost a worker; restart with @CWR@ workers (saved cells skipped) $(date +%H:%M)"
  step "convergence restart" 2.60
  uv run --frozen python docs/revision/followup2/convergence_v2.py --workers @CWR@ --site pod --out $O $IN $EV $PAID >> $L/f2_run.log 2>&1; drc=$?
  [ $drc = 5 ] && { echo "== RUN FAILED at convergence (a worker lost twice; saved cells kept) $(date +%H:%M)"; exit 1; }
fi
[ $drc = 4 ] && { echo "== GATE FAILED at convergence (round 1 differs) $(date +%H:%M)"; exit 1; }
[ $drc = 0 ] || { echo "== RUN FAILED at convergence $(date +%H:%M)"; exit 1; }
RB
)
RBODY=${RBODY//@CWR@/$CONVRETRY}; RBODY=${RBODY//@CW@/$CONVWORKERS}
fi
RS=$(mktemp "/tmp/${NAME}_remote.XXXXXX") || { state="CANNOT WRITE THE REMOTE SCRIPT"; exit 1; }   # private path (churn r1 review)
cat > "$RS" <<EOS
#!/bin/bash
R=\${REMOTE_ROOT:-/root}   # the pod's root; the offline harness runs this script under another root with a stub driver
echo "== remote started \$(date +%H:%M)"
cd \$R/touchstone || { echo "== RUN FAILED at setup \$(date +%H:%M)"; exit 1; }; export OMP_NUM_THREADS=1 PATH=\$HOME/.local/bin:\$PATH; unset TOUCHSTONE_IDENTITY_SALT; unset TOUCHSTONE_LOCKED
B=\$R/bundle; L=results/logs
IN="--src \$B/eval-all --draw \$B/draw/draw.json --instances \$B/draw/instances.json --cfgs \$B/deviation/cfg_linux.json --addendum \$B/report/addendum.json --report \$B/report/report.json"
PAID="--cap-usd $CAP --usd-per-hour $MAXCPH --started-at $a0 --attempts \$R/f2.attempts --ledger \$R/f2.ledger.json --run-tag $RUNTAG --stop-file \$R/STOP --soft-deadline $soft"
# step NAME HOURS: before a paid step, the launcher's STOP file and soft deadline, then the admission (guards.py admit;
# exit 3 = refused by the cap, the STOP file or the soft deadline); the step starts only on exit 0.
step() {
  { [ -e \$R/STOP ] || [ \$(date +%s) -ge $soft ]; } && { echo "== STOPPED BEFORE \$1 (cap) \$(date +%H:%M)"; exit 1; }
  uv run --frozen python docs/revision/followup2/guards.py admit \$PAID --hours \$2 >> \$L/f2_admit.log 2>&1; arc=\$?
  [ \$arc = 3 ] && { echo "== STOPPED BEFORE \$1 (cap, admission) \$(date +%H:%M)"; exit 1; }
  [ \$arc = 0 ] || { echo "== RUN FAILED at admission before \$1 \$(date +%H:%M)"; exit 1; }
  echo "== \$1 start \$(date +%H:%M)"
}
$RBODY
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
  if [ "$now" -ge "$soft" ] && [ -z "$stopped" ]; then tmo 60 $PY runpod.py ssh $id 'touch /root/STOP && test -e /root/STOP' >/dev/null 2>&1 && stopped=1 && echo "$(date +%H:%M) cap reached: the pod stops after the running step"; fi
  st=$(tmo 90 $PY runpod.py ssh $id "tail -c 240 /root/touchstone/results/logs/r_remote.log" 2>/dev/null | tr '\n' ' ')
  echo "$(date +%H:%M) [soft $(( soft - now ))s, hard $(( hard - now ))s] $st" | tail -c 320
  # the end state is the LAST "== ..." line of the polled tail (earlier lines of the joined tail are not part of it)
  last="$(echo "$st" | grep -o '== [A-Z][^=]*' | tail -n 1 | sed "s/[[:space:]]*\$//")"
  case "$last" in
    "== RUN OK"*) state="RUN OK"; rc=0; exit 0 ;;
    "== GATE FAILED"*|"== RUN FAILED"*|"== STOPPED BEFORE"*) state="$(echo "$last" | head -c 160)"; exit 1 ;;
  esac
done
