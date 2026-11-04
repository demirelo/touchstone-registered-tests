# H4 containment

H4 contains D2+H3 exactly. Keep `u0`, `m0`, `s`, `d`, `r`, `w`, `x`,
and `clip` unchanged. Set `k_F = k_T = 1`, `a_F = n_P = 0`, `e_P = 1`,
`b_gain = 0`, and `b_target = 1`. This gives the same markup recurrence,
cost bid, claim, effort, and failure-triggered reset. Markup persists across
identities. Set `x = 0` to embed D2. Also set `d = r = 0`, `u0 = u`, and
`m0 = m` to embed D1. H4 does not claim full containment of X7-SC or the
other existing families.

H4 adds bid feedback to state-conditioned inflation. After each eligible
round, the bid adjustment changes by
`b_gain * (own_served / own_capacity - b_target)`, bounded to `[-0.95, 2]`.
The adjustment persists across resets. It updates after a replacement round
even if no job was served. It skips banned rounds.

The fresh multiplier applies at low identity age, low own pass count, or
high recent own audit exposure. The terminal multiplier has priority during
the last `L` rounds. `clip = 1` clips every claim to effort, and the default
`Family.project` preserves the other knobs. The 15 knobs comprise 13 bounded
coordinates and the binary coordinates `x` and `clip`. Actions use only the
provider view and the injected `T` and `L`.
