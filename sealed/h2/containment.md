# H2 containment statement

Class: H2 contains D2.

Embedding: `embed_d2(knobs)` in `h2/family.py` maps a D2 point (u0, m0, s, d, r, w, clip) to the H2 point with the same values and g = 0, h = 0. At g = 0 the markup is m_eff = m_t, and at h = 0 the bid-markup state stays at w in every round. The H2 policy at the embedded point then gives the same action as the D2 policy in every round, for every history. The custodian checked this on 300 random D2 points and random histories of 12 rounds (exact equality of the action objects), before the commitment.

Twin: the twin of H2 is H2 with clip fixed at 1, which is a subset of H2, so H2 contains its twin by construction. The honest point (every bounded knob at its lower bound, clip = 1) gives the honest-max action in every round.

Observations and memory that H2 uses and D2 cannot:

1. Passed audits. H2 reads `history.audited` and `history.served` and estimates the audit frequency of its own served jobs, a_hat = (jobs audited so far) / (jobs served so far). It scales its markup to m_eff = m_t (1 - g a_hat). D2 reads only failed audits, so an audit that passes does not change D2.
2. Served counts. H2 reads `history.served` for the last round. If the entity was not banned in that round and served no job, it cuts its bid markup, w_t <- w_t (1 - h). If it served its full capacity k, it raises the markup back, w_t <- min(w, w_t + h w). D2 never reads served counts.
3. Memory. H2 keeps a second state variable, the bid markup w_t, in addition to the D2 markup state m_t. In D2 the bid markup is a constant.

H2 never abstains and never exits, like D2.
