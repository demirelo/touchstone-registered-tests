#!/bin/bash
# Throwaway smoke test of the Runpod v2 helpers. Deletes its pod on every exit path.
set -u
P=/Users/oemer.demirel/Projects/touchstone/results/pods
PY=/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79/.venv/bin/python
S=$(dirname "$0"); ID=""
ts(){ date -u +%FT%TZ; }
cleanup(){
  if [ -n "$ID" ]; then
    echo "$(ts) DELETE $ID"; $PY $P/runpod.py delete "$ID"
    for i in 1 2 3 4 5 6; do
      sleep 10
      if $PY $P/runpod.py list > $S/list_after.json; then
        if ! grep -q "\"$ID\"" $S/list_after.json; then echo "$(ts) GONE from list"; break; fi
      fi
      $PY $P/runpod.py delete "$ID"
    done
    echo "$(ts) get after delete:"; $PY $P/runpod.py get "$ID" | head -5
  fi
  echo "$(ts) END"
}
trap cleanup EXIT
echo "$(ts) PREFLIGHT"
$PY $P/runpod.py list > $S/list0.json || { echo "list failed"; exit 1; }; echo "list0: $(cat $S/list0.json | tr -d '\n ')"
$PY $P/runpod.py balance || { echo "balance failed"; exit 1; }
echo "$(ts) CREATE"
OUT=$($PY $P/create_one.py ts-diag 0); echo "create: $OUT"
ID=$($PY -c 'import json,sys; print(json.loads(sys.argv[1]).get("id",""))' "$OUT")
[ -n "$ID" ] || { echo "no pod id"; exit 1; }
for i in $(seq 1 60); do
  sleep 10
  G=$($PY $P/runpod.py get "$ID")
  if echo "$G" | grep -q '"publicIp": "[0-9]'; then echo "$(ts) READY after $((i*10))s"; echo "$G"; break; fi
done
echo "$(ts) LIST"; $PY $P/runpod.py list | tee $S/list1.json
echo "$(ts) SSH"; $PY $P/runpod.py ssh "$ID" 'echo smoke-ok; nproc; uname -m'
echo "$(ts) DF"; $PY $P/runpod.py ssh "$ID" "df -h / /root /workspace 2>&1; ls -la /root"
echo "$(ts) PUSH code"; time $PY $P/runpod.py push "$ID" $P/rep_code.tgz /root/rc.tgz; echo "$(ts) PUSH bundle2"; time $PY $P/runpod.py push "$ID" $P/rep_bundle2.tgz /root/rb.tgz; echo "$(ts) DF after"; $PY $P/runpod.py ssh "$ID" "df -h / /root; ls -la /root"
echo "$(ts) TESTS DONE"
