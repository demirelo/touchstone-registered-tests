# Publishing the Touchstone release (author steps)

Prepared 2026-11-05. Run each command yourself, in order, from a terminal. Nothing here was run by Claude. The current
repository `demirelo/touchstone` stays private; the steps create a new public repository with only the release branch
and the tag.

## Before you start: two decisions

1. **External review first (recommended).** The paper in the artifact is the one at commit 8dd9e5e. If the external
   review changes the paper, the artifact must be rebuilt after the last change (plan, Operation 9). Publish after the
   review.
2. **`sealed/` becomes public.** The branch history tracks `sealed/` (the first test's sealed attacker family, 8 files).
   Any push of this history publishes it. If it must stay private, stop here and tell Claude; the history would need a
   rewrite before publication, which also changes the tagged commit and needs a new plan.

## Steps

**1. Sign Claude's latest commits** (refuses unless the tag stays on the branch):

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && bash docs/revision/sign_after_tag.sh
```

Expected last line: `ok: tag on branch; unsigned commits after the tag: 0`.

**2. Check the artifact you will upload.** Expected: `f6cf682bda2fa5883ff35de00bea2228f2ee8e0c7f2b91168532968fec10812c`.

```bash
shasum -a 256 /Users/oemer.demirel/Projects/touchstone/results/v2/release/touchstone-v2.tar.gz
```

**3. Connect Zenodo before the release exists.** Zenodo archives a GitHub release only if the repository is switched on
in Zenodo first. Sign in at zenodo.org with GitHub, open Settings > GitHub, and switch on the new repository after
step 4 creates it (then continue with step 5).

**4. Create the public repository** (empty; nothing is pushed yet):

```bash
gh repo create demirelo/touchstone-registered-tests --public --description "Touchstone: two registered tests of age-ranked audit targeting under free identity replacement"
```

**5. Push the release branch as main, and the signed tag:**

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && git push git@github.com:demirelo/touchstone-registered-tests.git claude/vigorous-villani-bbac79:main refs/tags/protocol-v2
```

**6. Create the GitHub release with the artifact** (Zenodo archives it and mints the DOI):

```bash
cd /Users/oemer.demirel/Projects/touchstone/.claude/worktrees/vigorous-villani-bbac79 && gh release create v2.0 --repo demirelo/touchstone-registered-tests --title "Touchstone v2: second registered test" --notes-file docs/revision/release-notes.md /Users/oemer.demirel/Projects/touchstone/results/v2/release/touchstone-v2.tar.gz
```

**7. Tell Claude** the repository URL and the Zenodo DOI. Claude then puts them into the paper's availability sentence
(the `TODO at submission` marker) and rechecks the paper.
