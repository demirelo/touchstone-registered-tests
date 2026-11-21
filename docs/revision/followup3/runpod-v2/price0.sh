#!/bin/bash
# Smoke 2: is the price readable by podctl.py price at once after creation (as rep_pod.sh line 301 reads it)?
set -u
P=/Users/oemer.demirel/Projects/touchstone/results/pods
PY=/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79/.venv/bin/python
ID=""; ts(){ date -u +%FT%TZ; }
cleanup(){ if [ -n "$ID" ]; then echo "$(ts) DELETE"; cd $P && $PY podctl.py delete "$ID" 600; echo "podctl delete exit $?"; $PY runpod.py list; $PY runpod.py get "$ID" | head -3; fi; echo "$(ts) END"; }
trap cleanup EXIT
cd $P
$PY runpod.py list || exit 1
echo "$(ts) CREATE"; OUT=$($PY create_one.py ts-smoke2 0); echo "$OUT"
ID=$($PY -c 'import json,sys; print(json.loads(sys.argv[1]).get("id",""))' "$OUT"); [ -n "$ID" ] || exit 1
echo "$(ts) PRICE immediately: $($PY podctl.py price $ID; echo " exit $?")"
sleep 3; echo "$(ts) PRICE +3s: $($PY podctl.py price $ID; echo " exit $?")"
