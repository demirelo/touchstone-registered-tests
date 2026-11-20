#!/bin/bash
# Snapshot guard: run a private copy, so an edit to this file cannot reach a running launch.
if [ -z "${LAUNCH_SNAPSHOT:-}" ]; then
  export LAUNCH_SOURCE="$0"
  snapf="/Users/oemer.demirel/Projects/touchstone/results/pods/snap_$(basename "$0" .sh)_$$.sh"; cp "$0" "$snapf"
  LAUNCH_SNAPSHOT="$snapf" exec bash "$snapf" "$@"
fi
# The churn replication on new markets (docs/revision/followup3/replication-plan.md, plan section 5 to 7) on two Runpod CPU
# pods, one after the other. Generated from followup2_pod.sh (Run B, reviewed in follow-up launcher rounds r1-r3 and the
# rerun rounds; itself from churn_pod.sh and the reviewed reset_pod.sh, rounds r9-r18): pod safety, launch lock, price
# ceiling, watchdog, spend records, request-time attempts, the ledger snapshot, deadlines net of PRIOR, per-step
# admission, and verification of every pulled directory on every end state are unchanged. What differs (rep-launcher-notes.md):
# - The first argument selects the pod: 1 (instances, calibration, menus and references, C-thr(12)) or 2 (p = 0
#   evaluation, the churn-zero gate, churn searches and evaluation, continuation). Both pods share one run tag, one stop
#   cap (the spend card) and one pod name, ts-rep (implementation review r1): one launch lock for the whole replication,
#   and pod 2 is refused while pod 1's spend is unrecorded; pod 2 names pod 1's launch tag (POD1TAG), whose spend row
#   must be in the ledger and whose output must name it; the two launch tags differ.
# - Pod 1's bundle is the stamped manifest, its proof and the draw record; the code guard also requires that the manifest's
#   commit is an ancestor of EXPECT and that every file the manifest lists matches its hash in the tarball.
# - Pod 2's bundle adds pod 1's pulled output; the launcher verifies its inventory, that the calibration ran on Linux and
#   that the saved configurations match the calibration record, before any marker.
# - The driver (rep_v2.py) gets the stop cap, the ceiling, the pod's request time, PRIOR plus the closed attempts at the
#   ceiling, and the STOP file and soft deadline; its stage admissions (churn stages, continuation rounds) run inside each step.
# - After each pod, every file of the output directory is in its root inventory and verifies; every failure or stop exit
#   of the remote script writes the inventory first, and a pull that fails on a failure state is retried before deletion.
# - The launcher checks its own bytes against the manifest's rep_pod.sh before any marker.
# Spending (the author: do not kill jobs): at the cap the pod stops BETWEEN steps; only at HARD x the cap is the pod deleted
# mid-step (the watchdog). An EXIT/INT/TERM trap pulls what exists (only if the run started), deletes the pod and verifies
# it. Spend (r16): the record is the account balance difference (podctl.py spend NAME, at least an hour after the watchdog
# ends); this launcher prints only estimates. One launch per NAME at a time (NAME.launchlock; the watchdog releases it).
# Usage: rep_pod.sh <1|2> <code_tgz> <bundle_tgz> <tag> <cap_usd> <local_out>   (no spaces in paths)
# Env: EXPECT (commit inside the code tarball), MAXCPH, POD1TAG (pod 2 only: pod 1's launch tag), PUBH (the manifest's publication height, or "none": the draw is then
# recorded as nonconfirmatory), optional MINMEM (default 28), HARD (default 1.3), LEDGER (default the worktree's
# docs/revision/budget-ledger.json).
set -u
PY=/opt/homebrew/bin/python3; P=/Users/oemer.demirel/Projects/touchstone/results/pods
RUN=${1:?pod 1 or 2}; TGZ=${2:?code tarball}; BTGZ=${3:?bundle tarball}; TAG=${4:?tag}; CAP=${5:?cap_usd}; LOUT=${6:?local_out}; cd $P
case "$TGZ$BTGZ$TAG$LOUT" in *[[:space:]]*) echo "refused: a path or tag contains whitespace"; exit 1 ;; esac
# PLANCAP: the conservative estimate with 1.25 headroom at flag share 0.5 (cost_estimate.py: 32.13 USD), rounded up; the
# spend card sets the stop cap at or below it. One run tag for both pods, so the cap covers the whole replication.
case "$RUN" in
  1) NAME=ts-rep; RUNTAG=replication; PLANCAP=33.00; OUTS="followup3-rep"; POD1TAG="" ;;
  2) NAME=ts-rep; RUNTAG=replication; PLANCAP=33.00; OUTS="followup3-rep"; POD1TAG=${POD1TAG:-}
     [ -n "$POD1TAG" ] || { echo "refused: pod 2 needs POD1TAG, pod 1's launch tag"; exit 1; }
     case "$POD1TAG" in *[!A-Za-z0-9_.-]*) echo "refused: POD1TAG has characters other than letters, digits, _ . -"; exit 1 ;; esac
     [ "$POD1TAG" != "$TAG" ] || { echo "refused: pod 2's launch tag must differ from pod 1's ($POD1TAG)"; exit 1 ;} ;;
  *) echo "refused: the pod must be 1 or 2"; exit 1 ;;
esac
EXPECT=${EXPECT:?commit}; MAXCPH=${MAXCPH:?max usd per hour}; MINMEM=${MINMEM:-28}; HARD=${HARD:-1.3}
PUBH=${PUBH:?the manifest publication height, or none}
case "$PUBH" in none) PUBARG="" ;; *[!0-9]*|'') echo "refused: PUBH must be a block height or none"; exit 1 ;; *) PUBARG="--published-height $PUBH" ;; esac
# Workers (plan section 5 and 6): search 16, evaluation and doubling 9 (the churn arm's pod-side preflight lowers it on the
# pod), continuation 5; the drivers admit each against the pod's cgroup limit with 1.25 headroom over the Mac peak.
SEARCHW=16; EVALW=9; CONTW=5; CONTRETRY=3        # a lost continuation worker restarts the stage once on 3 workers
PEAKSEARCH=254115840   # bytes: the larger Mac peak of a full X7-SC menu search and a reference (rep-launcher-notes.md)
PEAKCONT=3540000000       # bytes: Run B's Mac peak of one X7-SC cell over three rounds (results/pods/memprobe3/rss.log); D2+H3 cells are smaller
LEDGER=${LEDGER:-/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79/docs/revision/budget-ledger.json}
[ -z "${PRIOR+x}" ] || { echo "refused: PRIOR is not an input here; it is the ledger's recorded spend for the run tag $RUNTAG"; exit 1; }
$PY -c "import math,sys; c=float(sys.argv[1]); p=float(sys.argv[2]); sys.exit(0 if math.isfinite(c) and 0 < c <= p else 1)" "$CAP" "$PLANCAP" 2>/dev/null || { echo "refused: the cap must be positive and at most the plan's $PLANCAP USD"; exit 1; }
# Rerun review r1 (Sol 5, Astra 4): the workers must fit the minimum pod memory (prep refuses a pod below MINMEM) at the
# measured peak per cell, with a margin of 1.25 and 2 GB for the driver process.
memfit() { $PY -c "import sys; w,p,m=int(sys.argv[1]),float(sys.argv[2])/1e9,float(sys.argv[3]); n=w*p*1.25+2; print(f'refused: {sys.argv[4]} with {w} workers needs about {n:.1f} GB ({w} x {p:.2f} GB peak x 1.25 + 2 GB for the driver), more than the {m:g} GB minimum pod memory') if n>m else None; sys.exit(3 if n>m else 0)" "$1" "$2" "$MINMEM" "$3" 2>/dev/null; r=$?
  [ $r = 0 ] && return 0; [ $r = 3 ] || echo "refused: the $3 memory check failed (workers $1, peak $2 bytes)"; return 1; }
memfit $SEARCHW "$PEAKSEARCH" search || exit 1; memfit $CONTW "$PEAKCONT" continuation || exit 1
LOGD=logs_rep${RUN}_$TAG; mkdir -p "$LOUT" $LOGD
$PY -c "import sys,tarfile; ms=tarfile.open(sys.argv[1]).getmembers(); d=[m.name for m in ms if m.name.split('/')[-1].startswith('._')]; o=[m.name for m in ms if m.uid!=0]; print('tarball guard: %d AppleDouble, %d non-root' % (len(d),len(o))); sys.exit(1 if d or o else 0)" "$TGZ" || { echo "code tarball refused"; exit 1; }
# Bundle guard: pod 1 needs the stamped manifest, its proof and the draw record; pod 2 also needs pod 1's output, whose
# inventory verifies, whose calibration ran on Linux and whose saved configurations match the calibration record.
BG=$(mktemp -d); tar xzf "$BTGZ" -C "$BG" 2>/dev/null || { echo "bundle refused: cannot unpack"; exit 1; }
$PY - "$BG" "$RUN" "$POD1TAG" "$LAUNCH_SNAPSHOT" <<'PYB' || { mv -- "$BG" ~/.Trash/bg_rep_$$; echo "bundle refused"; exit 1; }
import hashlib, json, sys
from pathlib import Path
b, run, pod1, me = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
bad = [f"draw/{n} missing" for n in ("manifest.json", "manifest.json.ots", "draw.json") if not (b / "draw" / n).is_file()]
if not bad:
    m = json.loads((b / "draw/manifest.json").read_text())
    if not (isinstance(m.get("commit"), str) and len(m["commit"]) == 40 and isinstance(m.get("files"), dict) and m["files"]):
        bad.append("draw/manifest.json has no commit or no file list")
    elif m["files"].get("docs/revision/followup3/rep_pod.sh") != hashlib.sha256(me.read_bytes()).hexdigest():
        bad.append("this launcher differs from the manifest's docs/revision/followup3/rep_pod.sh")
if run == "2" and not bad:
    r = b / "rep"
    try:
        recs = json.loads((r / "inventory.json").read_text())["records"]
        cal = json.loads((r / "calibration.json").read_text())
    except Exception:
        recs, cal = {}, {}
    sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
    wrong = [k for k, h in recs.items() if not (r / k).is_file() or sha(r / k) != h]
    extra = [str(q.relative_to(r)) for q in r.rglob("*") if q.is_file() and q.name != "inventory.json" and not q.name.endswith((".lock", ".tmp")) and str(q.relative_to(r)) not in recs]
    if not recs or wrong or extra:
        bad.append(f"rep/ inventory: {len(recs)} records, {len(wrong)} bad, {len(extra)} not inventoried")
    if cal.get("system") != "Linux" or cal.get("machine") not in ("x86_64", "AMD64"):   # plan section 1: Linux x86
        bad.append(f"rep/calibration.json was not made on Linux x86 ({cal.get('system')!r} {cal.get('machine')!r})")
    if not (r / "cfgs.json").is_file() or sha(r / "cfgs.json") != cal.get("cfgs_sha256"):
        bad.append("rep/cfgs.json does not match the calibration record")
    for n in ("instances.json", "salt.hex"):
        if not (r / n).is_file():
            bad.append(f"rep/{n} missing")
    try:                                  # pod 1's output belongs to this bundle's manifest and draw, and to launch POD1TAG
        bind, launch = json.loads((r / "binding.json").read_text()), json.loads((r / "launch.json").read_text())
    except Exception:
        bind, launch = {}, {}
    if bind != {"manifest_sha256": sha(b / "draw/manifest.json"), "draw_sha256": sha(b / "draw/draw.json")}:
        bad.append("rep/binding.json does not match this bundle's manifest and draw")
    if launch.get("launch") != pod1:
        bad.append(f"rep/launch.json names launch {launch.get('launch')!r}, not POD1TAG {pod1!r}")
print(f"bundle guard: pod {run}" + (f"; refused: {bad}" if bad else ": draw files present" + (", pod 1 output verified" if run == "2" else "")))
sys.exit(1 if bad else 0)
PYB
MCOMMIT=$($PY -c "import json,sys; print(json.load(open(sys.argv[1]))['commit'])" "$BG/draw/manifest.json"); cp "$BG/draw/manifest.json" "$P/${NAME}_manifest.$$.json"; MANF="$P/${NAME}_manifest.$$.json"
mv -- "$BG" ~/.Trash/bg_rep_$$
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
  # the commitment (plan section 5): the manifest's commit is in this history, and every listed file matches its hash
  git merge-base --is-ancestor "$MCOMMIT" HEAD || { echo "the manifest's commit $MCOMMIT is not an ancestor of HEAD"; return 1; }
  $PY - "$MANF" <<'PYK' || return 1
import hashlib, json, sys
from pathlib import Path
m = json.load(open(sys.argv[1]))
bad = [f for f, h in m["files"].items() if not Path(f).is_file() or hashlib.sha256(Path(f).read_bytes()).hexdigest() != h]
print(f"commitment: {len(m['files'])} listed files, {len(bad)} differ" + (f": {bad[:5]}" if bad else ""))
sys.exit(1 if bad else 0)
PYK
  echo "code guard: ok at $(git rev-parse --short HEAD)"
}
( guard "$hg" ); g=$?; mv -- "$hg" ~/.Trash/hg_rep_$$
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
PRIOR=$($PY - "$SNAP" "$RUNTAG" "$CAP" "$HARD" "$TAG" "$POD1TAG" <<'PYL'
import json, math, sys
led, tag, cap, hard, launch, pod1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5], sys.argv[6]
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
# Pod 2 counts pod 1's spend under the same run tag (one stop cap): pod 1's own spend row, by its launch tag, must be
# recorded first (an open pod 1 reservation also refuses below, as any earlier launch of the run does).
if pod1 and sum(1 for r in d["spent"] if str(r["tag"]) == f"{tag}-{pod1}") != 1:
    print(f"refused: pod 1's spend ({tag}-{pod1}) is not recorded in the ledger exactly once; record it first"); sys.exit(1)
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
      try=$((try+1)); ok=1; seen=0
      for d in $OUTS; do
        t=1800
        rem=$(( hard - 120 - $(date +%s) ))
        if [ $rem -le 0 ]; then ok=0     # no time left to pull, but still verify what is already on disk (rerun review r2)
        else [ $rem -lt $t ] && t=$rem; tmo $t $PY runpod.py pull $id "/root/touchstone/results/v2/$d/" "$LOUT/$d/" >/dev/null 2>&1 || ok=0; fi
        # verify whatever arrived, on every end state and after a failed or partial pull of this or another directory
        # (lessons.md: Run A went unverified after STOPPED; rerun review r1: one failed pull skipped every check)
        if [ -d "$LOUT/$d" ]; then seen=1; verify "$LOUT/$d" || ok=0; fi
      done
      rem=$(( hard - 120 - $(date +%s) )); [ $rem -gt 0 ] && tmo $(( rem < 300 ? rem : 300 )) $PY runpod.py pull $id /root/touchstone/results/logs/ $LOGD/ >/dev/null 2>&1
      [ $ok = 1 ] && break
      # implementation review r1: a failure state retries too (the remote writes its inventory on every failure exit),
      # so a partial pull is not deleted with the pod after one try
      echo "$(date +%H:%M) pull or verification failed (try $try)"
      if [ "$state" = "RUN OK" ]; then [ "$(date +%s)" -ge $(( hard - 120 )) ] && break
      else [ $try -ge 3 ] && { [ $seen = 1 ] && echo "$(date +%H:%M) end state $state: pulled records do not all verify after $try tries (see above)"; break; }; fi
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
chk=$(tmo 300 $PY runpod.py ssh $id "cd touchstone; export PATH=\$HOME/.local/bin:\$PATH; echo git=\$(git rev-parse HEAD 2>&1) env=\${TOUCHSTONE_IDENTITY_SALT:-unset} bundle=\$(ls /root/bundle/draw | wc -l); m=\$(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null); case \$m in max|''|9223372036854*) m=\$(awk '/MemTotal/ {print \$2*1024}' /proc/meminfo);; esac; echo memgb=\$((m/1073741824)); echo py=\$(uv run --frozen python -c 'import platform,numpy;print(platform.python_version(),numpy.__version__)' 2>&1 | tail -n 1 | tr ' ' _)" 2>/dev/null | tr '\n' ' ')
echo "$(date +%H:%M) prep: $chk"
case "$chk" in *"git=$EXPECT"*"env=unset"*) ;; *) state="PREP FAILED"; exit 1 ;; esac
memgb=$(echo "$chk" | sed -n 's/.*memgb=\([0-9]*\).*/\1/p'); [ -n "$memgb" ] && [ "$memgb" -ge "$MINMEM" ] || { state="PREP FAILED (memory ${memgb:-unknown} GB < $MINMEM GB)"; exit 1; }
# The admission inputs (plans section 5, launcher handoff): this launch's attempts file (closed attempts count at the
# ceiling; the open start is this pod's request time) and the ledger (earlier launches of the run tag). Both are fixed
# for the pod's life (no attempt event or ledger row can appear while it runs), so one push covers every paid step.
tmo 120 $PY runpod.py push $id "$ATT" /root/rep.attempts >/dev/null 2>&1 || { state="UPLOAD FAILED (attempts)"; exit 1; }
tmo 120 $PY runpod.py push $id "$SNAP" /root/rep.ledger.json >/dev/null 2>&1 || { state="UPLOAD FAILED (ledger)"; exit 1; }
# The driver's own admissions (churn stages, continuation rounds) count PRIOR plus this launch's closed attempts at the
# ceiling (guards.paid_cost_stop's rule), from the same fixed attempts file.
PRIORX=$($PY - "$ATT" "$PRIOR" "$MAXCPH" <<'PYX'
import sys
st, closed = {}, 0.0
for l in open(sys.argv[1]):
    f = l.split()
    if len(f) == 3 and f[2] == "start": st[f[0]] = float(f[1])
    elif len(f) == 3 and f[2] == "deleted" and f[0] in st: closed += float(f[1]) - st.pop(f[0])
print(round(float(sys.argv[2]) + closed / 3600 * float(sys.argv[3]), 6))
PYX
) || { state="PRIOR WITH ATTEMPTS UNKNOWN"; exit 1; }
# The run's own steps, kept literal ($ expands on the pod); inserted into the remote script below as one value.
if [ "$RUN" = 1 ]; then
RBODY=$(cat <<'R1'
step "instances" 0.05
uv run --frozen python $D --stage instances $IN --proof $B/draw/manifest.json.ots @PUBARG@ >> $L/rep.log 2>&1 || endinv "== RUN FAILED at instances"
printf '{"launch": "@TAG@"}\n' > $O/launch.json || endinv "== RUN FAILED at instances (launch record)"
step "calibrate" 0.25
uv run --frozen python $D --stage calibrate $IN >> $L/rep.log 2>&1 || endinv "== RUN FAILED at calibrate"
step "menu" 7.60
uv run --frozen python $D --stage menu $IN $RP --workers-search @SW@ --peak-search @PS@ >> $L/rep.log 2>&1 || endinv "== RUN FAILED at menu"
step "cthr" 1.95
uv run --frozen python $D --stage cthr $IN $RP --workers-search @SW@ --peak-search @PS@ >> $L/rep.log 2>&1 || endinv "== RUN FAILED at cthr"
uv run --frozen python $D --stage inventory $IN >> $L/rep.log 2>&1 || { echo "== RUN FAILED at inventory $(date +%H:%M)"; exit 1; }
R1
)
else
RBODY=$(cat <<'R2'
mkdir -p results/v2 && cp -a $B/rep $O || endinv "== RUN FAILED at setup (pod 1 output)"
# churn_v2 stops between its stages at the cap with a message (exit 1): read as a stop, not a failure
stopped() { tail -n 5 $L/rep.log | grep -q "churn arm stopped between stages"; }
# admission hours from cost_estimate.py (schedule at flag share 0.5): rates p0 = p = 0 evaluation and doubling 1.62 +
# its diagnostics 0.06; rates churn = churn search 4.62 + evaluation and doubling 4.31 + diagnostics 0.12
step "rates p0" 1.68
uv run --frozen python $D --stage rates --rates p0 $IN $RP --workers-search @SW@ --peak-search @PS@ --workers-eval @EW@ >> $L/rep.log 2>&1 || {
  if stopped; then endinv "== STOPPED BEFORE a rates p0 stage (cap, driver admission)"; else endinv "== RUN FAILED at rates p0"; fi; }
step "gate0" 1.20
uv run --frozen python $D --stage gate0 $IN $RP --workers-search @SW@ --peak-search @PS@ --workers-eval @EW@ >> $L/rep.log 2>&1 || {
  if tail -n 5 $L/rep.log | grep -q "the churn-zero gate failed"; then endinv "== GATE FAILED at gate0 (churn path not bit-identical at p = 0)"
  elif stopped; then endinv "== STOPPED BEFORE a gate0 stage (cap, driver admission)"; else endinv "== RUN FAILED at gate0"; fi; }
echo "== gate0 passed (bit-identical) $(date +%H:%M)"
step "rates churn" 9.05
uv run --frozen python $D --stage rates --rates churn $IN $RP --workers-search @SW@ --peak-search @PS@ --workers-eval @EW@ >> $L/rep.log 2>&1 || {
  if stopped; then endinv "== STOPPED BEFORE a rates churn stage (cap, driver admission)"; else endinv "== RUN FAILED at rates churn"; fi; }
# continuation: the launcher admits the gate cell's round (0.41 h + 0.1 h shutdown); every later round is admitted inside
step "continue" 0.51
uv run --frozen python $D --stage continue $IN $RP --workers-cont @CW@ --peak-cont @PC@ >> $L/rep.log 2>&1; drc=$?
if [ $drc = 5 ]; then                  # a lost worker: the finished cells are saved; one restart on fewer workers runs the rest
  echo "== continue lost a worker; restart with @CWR@ workers (saved cells skipped) $(date +%H:%M)"
  RH=$(grep -o '[{ ,]"@CWR@": [0-9.]*' $O/continuation/lost_cells.json 2>/dev/null | head -n 1 | sed 's/.*: //')
  [ -n "$RH" ] || endinv "== RUN FAILED at continue restart (no restart estimate in lost_cells.json)"
  step "continue restart" $RH
  uv run --frozen python $D --stage continue $IN $RP --workers-cont @CWR@ --peak-cont @PC@ >> $L/rep.log 2>&1; drc=$?
  [ $drc = 5 ] && endinv "== RUN FAILED at continue (a worker lost twice; saved cells kept)"
fi
[ $drc = 3 ] && endinv "== STOPPED BEFORE a continuation round (cap, driver admission)"
[ $drc = 4 ] && endinv "== GATE FAILED at continue (round 1 differs from this run's doubling record)"
[ $drc = 6 ] && endinv "== RUN FAILED at continue (a cell error; see continuation records)"
[ $drc = 0 ] || endinv "== RUN FAILED at continue"
uv run --frozen python $D --stage inventory $IN >> $L/rep.log 2>&1 || { echo "== RUN FAILED at inventory $(date +%H:%M)"; exit 1; }
R2
)
fi
RBODY=${RBODY//@CWR@/$CONTRETRY}; RBODY=${RBODY//@CW@/$CONTW}; RBODY=${RBODY//@SW@/$SEARCHW}; RBODY=${RBODY//@EW@/$EVALW}
RBODY=${RBODY//@PS@/$PEAKSEARCH}; RBODY=${RBODY//@PC@/$PEAKCONT}; RBODY=${RBODY//@PUBARG@/$PUBARG}; RBODY=${RBODY//@TAG@/$TAG}
RS=$(mktemp "/tmp/${NAME}_remote.XXXXXX") || { state="CANNOT WRITE THE REMOTE SCRIPT"; exit 1; }   # private path (churn r1 review)
cat > "$RS" <<EOS
#!/bin/bash
R=\${REMOTE_ROOT:-/root}   # the pod's root; the offline harness runs this script under another root with a stub driver
echo "== remote started \$(date +%H:%M)"
cd \$R/touchstone || { echo "== RUN FAILED at setup \$(date +%H:%M)"; exit 1; }; export OMP_NUM_THREADS=1 PATH=\$HOME/.local/bin:\$PATH; unset TOUCHSTONE_IDENTITY_SALT TOUCHSTONE_LOCKED TOUCHSTONE_PROPOSED_MODULE TOUCHSTONE_PROPOSED_PARAMS TOUCHSTONE_SEALED_DIR TOUCHSTONE_GIT_COMMIT
B=\$R/bundle; L=results/logs; O=results/v2/followup3-rep; D=docs/revision/followup3/rep_v2.py
IN="--out \$O --manifest \$B/draw/manifest.json --draw \$B/draw/draw.json"
RP="--started $a0 --usd-per-hour $MAXCPH --stop-usd $CAP --prior-usd $PRIORX --stop-file \$R/STOP --soft-deadline $soft"
PAID="--cap-usd $CAP --usd-per-hour $MAXCPH --started-at $a0 --attempts \$R/rep.attempts --ledger \$R/rep.ledger.json --run-tag $RUNTAG --stop-file \$R/STOP --soft-deadline $soft"
# step NAME HOURS: before a paid step, the launcher's STOP file and soft deadline, then the admission (guards.py admit;
# exit 3 = refused by the cap, the STOP file or the soft deadline); the step starts only on exit 0.
# endinv LINE: every failure or stop exit writes the output's inventory first (implementation review r1), so that what was
# pulled verifies; the end line stays the log's last line, which the launcher reads as the end state.
endinv() {
  [ -d \$O ] && uv run --frozen python \$D --stage inventory \$IN >> \$L/rep.log 2>&1
  echo "\$1 \$(date +%H:%M)"; exit 1
}
step() {
  { [ -e \$R/STOP ] || [ \$(date +%s) -ge $soft ]; } && endinv "== STOPPED BEFORE \$1 (cap)"
  uv run --frozen python docs/revision/followup2/guards.py admit \$PAID --hours \$2 >> \$L/rep_admit.log 2>&1; arc=\$?
  [ \$arc = 3 ] && endinv "== STOPPED BEFORE \$1 (cap, admission)"
  [ \$arc = 0 ] || endinv "== RUN FAILED at admission before \$1"
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
  # split on the " == " marker only: a state may itself contain "=" (the gate0 state says "p = 0")
  last="== ${st##*== }"; last="$(echo "$last" | sed "s/[[:space:]]*\$//")"
  case "$last" in
    "== RUN OK"*) state="RUN OK"; rc=0; exit 0 ;;
    "== GATE FAILED"*|"== RUN FAILED"*|"== STOPPED BEFORE"*) state="$(echo "$last" | head -c 160)"; exit 1 ;;
  esac
done
