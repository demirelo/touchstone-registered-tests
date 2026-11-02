# Lessons, revision program (protocol v2)

Read this before any operations step. One entry per mistake: what happened, the guard that now prevents it, and the guard's kind (check > written rule > memory note). A repeated mistake means its guard failed: replace it with a stronger kind.

| Date | Mistake | Guard | Kind |
|---|---|---|---|
| 2026-10-28 | The pod tarball carried the laptop user's uid; git on the pod refused the repository ("dubious ownership") and all three tuning pods failed their prep check. | Build every pod tarball with `tar --uid 0 --gid 0`. The launcher's prep check (`git=<commit>`) already fails safe before any run. | check (prep) + rule |
| 2026-10-28 | The launcher's seed push targets a remote directory that does not exist before the run; `comparator.json` never reached the C*-t pod and the run failed at start. | Put every input a pod run needs inside the tarball (under a git-ignored path if it is not tracked); do not use the seed argument. | rule |
| 2026-10-28 | A zsh loop used `set -- $t` to split a string; zsh does not word-split, so every budget reservation failed on its arguments. | Write budget and launch commands out explicitly, one per line; do not split strings into arguments in zsh. | rule |
| 2026-11-02 | The approval commit added a `.gitignore` line; `.gitignore` is outside the data-only paths, so every later commit failed `promote_v2.same_code` and coverage refused the checkout. | Restored `.gitignore` (91c80ff); the lock file is excluded through `.git/info/exclude`. A pre-commit hook refuses, on `claude/vigorous-villani-bbac79` and on any detached HEAD after `h4-base`, a staged path outside `experiments/v2/` and `docs/` (negative tests on the branch and on a detached HEAD: refused). | check (hook) |
| 2026-11-02 | The worktree's HEAD was detached after the ledger commit (unlabelled checkout in the reflog); a commit landed off the branch, and the first version of the hook skipped detached HEADs. | The hook now applies to detached HEADs after `h4-base`; check `git status -sb` before committing on this branch. | check (hook) + rule |
| 2026-10-28 | The H4 session command wrote only a mixed log; when the machine restarted, the session died and the final message had no file of its own. | The resume command uses `-o ~/h4-final.txt`; read only that file. | rule |
