#!/usr/bin/env bash
# Operation 5, the author's steps, in order: sign, stamp, push, upgrade (repeat until attested), tag.
# Run from anywhere: bash <worktree>/docs/revision/operation5.sh <step>. Each step checks its precondition and refuses otherwise.
set -euo pipefail
W=/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79
B=claude/vigorous-villani-bbac79
P=experiments/protocol-v2.yaml
OTS=(uvx --from opentimestamps-client ots)  # the form in docs/lock-runbook.md; no global install needed
cd "$W"
die() { echo "refused: $*" >&2; exit 1; }
# Signing or stamping after the tag rewrites the registered history; once the tag exists, every step refuses.
git rev-parse -q --verify refs/tags/protocol-v2 >/dev/null && die "Operation 5 is finished: tag protocol-v2 exists ($(git rev-parse --short 'protocol-v2^{commit}'))"
[ "$(git branch --show-current)" = "$B" ] || die "the worktree is not on $B"
[ -z "$(git status --porcelain --untracked-files=no -- . ":!$P.ots")" ] || die "tracked changes other than $P.ots"
unsigned() { git log --format='%G? %h %s' h4-base..HEAD | grep -v '^G' || true; }
attested() { "${OTS[@]}" info "$P.ots" 2>/dev/null | grep -qi 'BitcoinBlockHeaderAttestation'; }
case "${1:-}" in
  sign)
    [ -n "$(unsigned)" ] || die "nothing to sign: every commit after h4-base is signed"
    git rebase --exec 'git commit --amend --no-edit -S' h4-base "$B"
    [ -z "$(unsigned)" ] || die "still unsigned: $(unsigned)"
    echo "ok: every commit after h4-base is signed" ;;
  stamp)
    [ -z "$(unsigned)" ] || die "sign first (step sign); unsigned: $(unsigned)"
    [ ! -e "$P.ots" ] || die "$P.ots exists already"
    uv run python scripts/lock_v2.py --check
    "${OTS[@]}" stamp "$P"
    git add "$P.ots"
    git commit -S -m "Operation 5: OpenTimestamps proof (pending)"
    echo "ok: stamped; next: push" ;;
  push)
    [ -z "$(unsigned)" ] || die "sign first; unsigned: $(unsigned)"
    git push --force-with-lease origin "$B"  # the branch was pushed once before signing; signing rewrote it
    echo "ok: pushed" ;;
  upgrade)
    [ -e "$P.ots" ] || die "stamp first"
    "${OTS[@]}" upgrade "$P.ots" || true
    if attested; then "${OTS[@]}" info "$P.ots" | grep -i 'BitcoinBlockHeaderAttestation'; echo "ok: attested; next: tag"
    else echo "pending: no Bitcoin attestation yet; run upgrade again in an hour or two"; fi ;;
  tag)
    attested || die "no Bitcoin attestation yet (step upgrade)"
    git add "$P.ots"
    git diff --cached --quiet || git commit -S -m "Operation 5: OpenTimestamps proof (Bitcoin attested)"
    [ -z "$(unsigned)" ] || die "unsigned: $(unsigned)"
    uv run python scripts/lock_v2.py --check
    git tag -s protocol-v2 -m "Protocol v2"
    git push origin "$B" protocol-v2
    echo "ok: tagged and pushed; tell Claude 'done'" ;;
  *) die "usage: operation5.sh sign|stamp|push|upgrade|tag" ;;
esac
