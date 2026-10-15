# Development families D1 and D2 (executable definitions)

Code: `sim/policies/fixed_cheat.py` (D1), `sim/policies/adaptive.py` (D2),
`sim/policies/families.py` (knobs, bounds, transforms, projection, corners,
registered starts), `sim/policies/identity.py` (H3 wrapper and the D2+H3
family).

D1 fixed cheat. Knobs u, m in [0, 1], s in [0, 0.3], w in [0, 2], clip in
{0, 1}. Effort q = q_max (1 - u); claim c = min(1, max(0, q + m - s)); with
clip = 1 the claim is min(c, q); bid = (1 + w)(a + b q). Never abstains or
exits.

D2 adaptive cheat. Knobs u0, m0 in [0, 1], s in [0, 0.3], d in [0, 1], r in
[0, 0.2], w in [0, 2], clip in {0, 1}. State m_t with m_1 = m0; effort
q = q_max (1 - u0); claim as D1 with m_t; after a round with a failed audit
m_{t+1} = m_t (1 - d), otherwise m_{t+1} = min(m0, m_t + r m0); unchanged
during a ban. D2 contains D1 at d = r = 0 (`embed_d1_in_d2`).

D2+H3 (stress test, spec 6.2). D2 plus a binary knob x: with x = 1 the
policy exits in the round after a failed audit and re-enters under a fresh
identity in that round at cost e; with x = 0 it never exits. Its honest
point (x = 0, clip = 1) is honest-max, so the reference is contained.
Reading the H3 table: a rule cannot link a fresh identity to its
predecessor through ids, offer order, tie-break keys, or audited
deliveries (all salted or ordered by id). Two links remain and are
inherent: in a registered H3 cell only the focal entity exits, so the
timing of one identity going silent and one appearing identifies the
newcomer; and the newcomer's offer reflects its provider type, which
with ten distinct provider types identifies the entity. Gains in the H3
table are therefore against rules that could, in principle, treat a
newcomer by timing or by type; the salted channels matter for rules that
would exploit more (several simultaneous exits, identical types).

Transform. Search coordinate in R^dim; bounded knob = lo + (hi - lo)
sigmoid(x); a binary knob (clip, x) is 1 iff sigmoid(x) >= 0.5. Exact
points (corners, the honest point, registered incumbents) are evaluated
from knob dictionaries, never through the inverse transform; the archive
keys points by their exact values.

Registered starts (spec 5.3), in this order for attack searches:
near-full-cheat (logit 0.98 on every coordinate, s and clip at logit
0.02); near-honest (logit 0.02 on every coordinate, clip at logit 0.98);
three scrambled Sobol points with seed `search.sobol_seed` from
`locked.yaml`. Twin searches swap the first two. A search with one
restart (inner tuning, all-deviators) uses the first start only. Honest point: every bounded knob at
its lower bound, every binary knob 0 except clip = 1; it reproduces
honest-max (`tests/test_families.py`).

Projection: clip set to 1, every other knob unchanged. Twins are the
families with clip fixed at 1. Containment tests: `tests/test_families.py`,
`tests/test_reference.py`.
