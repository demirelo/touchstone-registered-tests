#!/usr/bin/env bash
# Prepare a fresh CPU pod (Runpod or similar) for Touchstone runs. Usage: bash scripts/pod_setup.sh [repo-url] [branch]
set -euo pipefail
REPO="${1:-git@github.com:demirelo/touchstone.git}"
BRANCH="${2:-main}"
if [ ! -d touchstone ]; then git clone --branch "$BRANCH" "$REPO" touchstone; fi
cd touchstone
command -v uv >/dev/null 2>&1 || pip install uv
uv sync
export OMP_NUM_THREADS=1
echo "export OMP_NUM_THREADS=1" >> ~/.bashrc
nproc 2>/dev/null || sysctl -n hw.ncpu
echo "ready: run the commands of docs/lock-runbook.md (Pods section) from $(pwd)"
