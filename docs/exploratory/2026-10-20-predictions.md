# Predictions for the six exploratory attackers (written 2026-10-20, before any outcome-producing simulation)

Status: exploratory. Plan `docs/superpowers/plans/2026-10-20-exploratory-attackers.md` (v3). These predictions are committed before the implementation commits that can produce a market outcome (no smoke run, no fixture market has been run with these families). The dev-val seeds have informed earlier development of the baselines and of R3, so dev-val is not a fresh holdout; results are descriptive (n = 20, no coverage admission).

## Anchors (registered dev-val, headline cell: beta 0.05, rho 0.2, median position, 20 seeds)

| Rule | D2 mean gain | D2+H3 mean gain |
|---|---|---|
| B1 | 0.409 | 0.409 |
| B2 | 0.009 | 0.581 |
| B3 | 0.040 | 0.357 |
| R3 | 0.041 | 0.070 |

Facts used: B1 audits nothing; B2 and B3 audit uniformly at random (about 21 percent of served jobs per round at this budget) with tolerance 0.16 and a 10-round ban; R3 audits about 10 or 11 jobs per early round, first every served job of identities younger than 10 rounds (priority), then half newest-first (T1) and half uniform, and every served job in the last 10 rounds. Entry is free (e = 0). Under T1 a replacement identity stays newer than the ten initial identities after it ages out of the priority window, so it remains first in the targeted half.

## Predictions (mean gain at the selected attack point; "about" means within roughly 0.05)

1. **B1, every family:** about 0.41; the gates are inert (no audits), the search finds always-cheat; X6 adds nothing at any c.
2. **X1 audit-hazard and X2 tranche signal.** B2 and B3: with x = 1 they reach about the D2+H3 level (B2 about 0.55, B3 about 0.33), since uniform audits give no phase signal and replacement escapes the ban. R3: about 0.04 to 0.07; the learned hazard is near 1 in fresh and terminal phases and near 0.2 when established, so they cheat only as established identities, which is what D2 already does; a reset re-enters the priority window and the newest-first targeting.
3. **X3 horizon timing (no exits).** B2 and B3: about the D2 level (0.01 to 0.05); terminal cheating pays a little under uniform audits because a ban near the end costs few rounds. R3: about 0.04; the search avoids the terminal window, where every served job is audited (the [190, 200) diagnostic should lose money against R3 and gain slightly against B2 and B3).
4. **X4 reset option and X5 aging.** B2 and B3: about the D2+H3 level, with n_age near 0 (aging buys nothing under uniform audits) and resets kept. R3: about 0.05 to 0.10; aging past the 10-round window removes the priority audits, but the aged replacement is still first in R3's newest-first targeted half, so a modest gain over D2+H3 at most; the selected n_age should sit near 10 if the window matters, and the reset option should prefer waiting out bans late in the episode.
5. **X6 simultaneous entrants.** c = 1 reproduces X5-like numbers (control). B2 and B3: about the D2+H3 level at every c (no quota to exhaust). R3: the priority quota (about 10 or 11 audits) is exhausted when two or more six-job identities are fresh at once, so c = 2 should raise the focal gain above c = 1 (prediction: 0.10 to 0.20) and c = 5 further (prediction: 0.20 to 0.35, approaching B3's D2+H3 level), with the staggered control lower than the synchronised one at the same reset count. This is the test most likely to show a real weakness of R3; it is the quota's capacity limit stated in amendment 3's risks.

## What would surprise us

Any family beating 0.30 against R3 at c = 1; X3 gaining against R3 in the terminal window; X6 at c = 5 not exceeding c = 1 against R3; any honest point or twin diverging from honest-max (that would be a bug, not a result).
