#!/usr/bin/env bash
# Prepare a fresh CPU pod (Runpod or similar) for Touchstone runs.
# Usage: bash scripts/pod_setup.sh <repo-url> <branch>      (HTTPS URL for a fresh pod with no SSH key; both arguments required)
set -euo pipefail
REPO="${1:?repo url, for example https://github.com/demirelo/touchstone.git}"
BRANCH="${2:?branch to run, for example plan-2b}"
if [ ! -d touchstone ]; then git clone --branch "$BRANCH" "$REPO" touchstone; fi
cd touchstone
git checkout -q "$BRANCH"
command -v uv >/dev/null 2>&1 || pip install uv
uv sync
export OMP_NUM_THREADS=1
grep -q OMP_NUM_THREADS ~/.bashrc 2>/dev/null || echo "export OMP_NUM_THREADS=1" >> ~/.bashrc
echo "cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu)"
echo "ready: copy experiments/tuned and the calibrations here, then run the Pods section of docs/lock-runbook.md from $(pwd)"
