#!/bin/bash
# Move each path to ~/.Trash under a unique name. Fails (exit 1) and moves nothing more if any move fails,
# so a caller chained with && never goes on to overwrite the paths it meant to keep.
set -u; [ $# -ge 1 ] || { echo "trash: no paths"; exit 1; }
for p in "$@"; do
  [ -e "$p" ] || { echo "trash: missing $p"; exit 1; }
  dst="$HOME/.Trash/$(basename -- "$p").$(date -u +%Y%m%dT%H%M%SZ).$$"
  mv -- "$p" "$dst" || { echo "trash: move failed for $p"; exit 1; }
  [ ! -e "$p" ] || { echo "trash: $p still present"; exit 1; }
done; echo "trash ok ($# paths)"
