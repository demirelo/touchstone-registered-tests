#!/bin/bash
# Signs every commit after tag protocol-v2 on this branch (lesson 2026-11-05: a signing rebase from an earlier base
# rewrote the tagged commit). The base is the tag itself; the script refuses to start, and fails after, unless the
# tagged commit is on the branch. Usage: bash docs/revision/sign_after_tag.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git merge-base --is-ancestor protocol-v2 HEAD || { echo "refused: protocol-v2 is not on this branch"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "refused: uncommitted changes"; exit 1; }
git rebase --exec 'git commit --amend --no-edit -S' protocol-v2
git merge-base --is-ancestor protocol-v2 HEAD || { echo "FAILED: the tag left the branch; restore with git reset --hard ORIG_HEAD"; exit 1; }
n=$(for c in $(git rev-list protocol-v2..HEAD); do git cat-file commit "$c" | grep -q gpgsig || echo "$c"; done | wc -l | tr -d ' ')
echo "ok: tag on branch; unsigned commits after the tag: $n"
