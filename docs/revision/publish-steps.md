# Publishing the Touchstone release (author steps)

Rewritten 2026-11-24 (replaces the 2026-11-05 version). Run each command yourself, in order, from a terminal. Nothing
here was run by Claude. The repository `demirelo/touchstone` stays private; the steps create a new public repository with
the release branch and the record tags. Decided on 2026-11-24: `sealed/` (the first test's H2 family, unsealed on 18
October) is published with the history.

W=/Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79
R=/Users/oemer.demirel/Projects/touchstone/results/v2

**1. Sign Claude's commits.** Signing rewrites the commit ids after `origin/main`, never the content. Note the tree first:

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && git rev-parse HEAD^{tree}
```

Write the printed hash down. Then sign:

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && bash docs/revision/sign_after_tag.sh && git rev-parse HEAD^{tree}
```

Expected: `ok: tag on branch; unsigned commits after the tag: 0`, then the same tree hash you wrote down.

**2. Check the seven release files.**

```bash
cd /Users/oemer.demirel/Projects/touchstone/results/v2 && shasum -a 256 release/touchstone-v2.tar.gz release-followups/*.tar.gz
```

Expected: the hashes in `docs/revision/release-notes.md`. Then the follow-up manifests:

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && uv run python docs/revision/release/followups.py --check /Users/oemer.demirel/Projects/touchstone/results/v2/release-followups
```

Expected: six lines ending in `ok`.

**3. Connect Zenodo before the release exists.** Zenodo archives a GitHub release only if the repository is switched on
in Zenodo first. Sign in at zenodo.org with GitHub, open Settings > GitHub, and switch on the new repository after
step 4 creates it (then continue with step 5).

**4. Create the public repository** (empty; nothing is pushed yet):

```bash
gh repo create demirelo/touchstone-registered-tests --public --description "Touchstone: two registered tests of age-ranked audit targeting under free identity replacement"
```

**5. Push the branch as main, and the nine record tags:**

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && git push git@github.com:demirelo/touchstone-registered-tests.git claude/vigorous-villani-bbac79:main refs/tags/lock-2026-10-17 refs/tags/lock-2026-10-17-amendment-1 refs/tags/lock-2026-10-17-amendment-2 refs/tags/lock-2026-10-17-amendment-3 refs/tags/lock-2026-10-17-amendment-4 refs/tags/freeze-2026-10-18 refs/tags/final-eval-2026-10-20 refs/tags/h4-base refs/tags/protocol-v2
```

**6. Create the GitHub release with the seven files** (Zenodo archives it and mints the DOI):

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && gh release create v2.1 --repo demirelo/touchstone-registered-tests --title "Touchstone: two registered tests, follow-ups and replication" --notes-file docs/revision/release-notes.md /Users/oemer.demirel/Projects/touchstone/results/v2/release/touchstone-v2.tar.gz /Users/oemer.demirel/Projects/touchstone/results/v2/release-followups/*.tar.gz
```

**7. Tell Claude** the repository URL and the Zenodo DOI. Claude then puts them into the paper's availability sentence
(the `TODO at submission` marker), rechecks the paper, and you sign and push that last commit.

Checks already done by Claude on 2026-11-24 (no external effect):
- `touchstone-v2.tar.gz` still reproduces the second test's report from a clean clone of this branch (`reproduce_deviation.py`: ok).
- Each follow-up archive was built by `docs/revision/release/followups.py` (explicit folder list; refuses `sealed` and `mac_diag` paths) and passes `--check`.
- The replication archive, unpacked alone, rebuilds the paper extract byte for byte (records digest `51086341…`).
- Secret scan: the tracked files (pattern scan) and all 702 commits (`gitleaks git`, `sealed/` excluded from the log): no findings.
