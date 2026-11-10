VERDICT: reject

CORRECTIONS:
1. **None — plan §3, tolerance deviation.** The change is justified and explicitly recorded. Both saved reproductions pass the current comparator: maximum knob drift is 2.58e-13 relative; maximum gain drift is 2.02e-14 absolute. The plan now states the corner-control discrepancy and avoids attributing all drift to the optimizer. Pairing, code, salt, input conflicts, freeze membership, acceptance, output protection, and environment checks address the specified round-4 findings.

2. **Plan §§3(d), 8.3; `reset_followup_v2.py:417–428` — block pod creation until current validation records exist.** The saved doubling output passes the numerical comparison, but lacks provenance and dependency hashes; its directory has no inventory. Its saved gate predates the corrected reproduction path. Both headline reproduction directories also lack `gate.json` and inventories. Run the corrected validation paths and retain their required records before provisioning. An old numerical pass does not establish that the new preflight ran.

3. **Plan §§4, 8; `reset_followup_v2.py:46–51,482–496`.** Add an explicit execution path for all three headline diagnostic cells on all 200 seeds. The documented Mac command covers only six fresh markets; `--markets headline` is refused because headline cells were retained. The existing headline test covers F111 on two seeds. Thus, the instructions do not deliver the promised seven-market, 63-policy diagnostic coverage.

4. **`reset_followup_v2.py:383`; plan §3.** Qualify `identical` as “selected knobs and gains identical,” or require objective equality too. An in-memory check with changed control objectives still returned `identical: true`. That result must not be reported as full bit identity.

5. **None — plan §§4–6.** Reverse-switch construction, saved per-seed diagnostics, zero-reset enforcement, separate five-market denominator gates, base/doubled reporting, all-six-market scoring, and the explicit best-of deferral are clear.

CONFIDENCE: 0.96.