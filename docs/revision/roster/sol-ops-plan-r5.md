VERDICT: reject

FINDINGS:

References to “plan” mean `docs/superpowers/plans/2026-10-25-revision-operations.md`.

1. **Important — Task 8, plan:118,258; `scripts/revision_v2.py:75,834`.** The verification test still does not prohibit every filesystem write. Patching `builtins.open` and `os.open` does not intercept `Path.write_text()`, which uses `io.open`. Directory creation also bypasses these patches. A wrong verifier can write a cache or create directories while passing the specified guards. An in-memory probe confirmed the `Path.write_text()` bypass without writing a file. **Repair:** guard `io.open` and filesystem mutation operations, or use a process audit guard. Inject prohibited writes through `Path.write_text()` and directory creation, including outside `--out`, and assert that the guard rejects them. The calibration, first-best, loader, and salt-reader alias corrections are complete; the broader write prohibition remains partly closed.

2. **Important — Task 4, plan:75–76.** The concurrent reservation test permits a false pass. An estimate of USD 2 normally reserves USD 2.50, so USD 10 permits four successful reservations. The test allows five successes and checks only the committed aggregate. Without locking, two writers can overwrite one reservation; five callers then receive USD 12.50 in caps while the ledger records four reservations totalling USD 10. Both stated assertions pass. **Repair:** assert that successful returned grants sum to at most USD 10, that every successful reservation exists exactly once in the ledger, and that at most four requests succeed. Add a controlled read/write interleaving that exposes a lost update.

The other round-4 corrections address their stated failures: Task 7 consumes unchanged JSON from `block_draw.main` (plan:107); Task 8 requires completion barriers and checks recorded calls against `dispatch_plan` (116–118); Task 4 tests unequal durations and the combined approval boundary (74–76). These tests target the previously identified wrong implementations.

Both rulings remain accepted. Task 9 reports search-incomplete doubling labels without changing decisions, with a paired-label test (plan:128–130). Task 8 preserves the complete freeze before evaluation and adds priority barriers within stages (116–118), consistent with the spec’s freeze requirement (`docs/superpowers/specs/2026-10-22-revision-program-design.md:249–253`).

Sol round-4 finding 1: **closed** — combined live approval limit and crossing test, plan:75–76.  
Sol round-4 finding 2: **closed** — producer JSON includes the digest, plan:107.  
Sol round-4 finding 3: **closed** — actual calibration and salt aliases, plus first-best execution, are prohibited, plan:118.  
Sol round-4 finding 4: **closed** — explicit completion barriers replace submission-order checks, plan:116–118.

Astra round-4 finding 1: **partly closed** — calibration aliases are covered; filesystem guards remain incomplete, finding 1.  
Astra round-4 finding 2: **closed** — conservative wave bound and unequal-duration tests, plan:74–76.  
Astra round-4 finding 3: **closed** — live combined approval gate, plan:75–76.  
Astra round-4 finding 4: **closed** — tier waves and completion-event assertions, plan:116–118.

Previously partial Sol round-1 findings: **S1 closed; S2 closed; S4 closed; S6 closed; S7 closed at the interface-contract level; S11 closed; S12 closed; S14 partly closed** because findings 1–2 leave false-pass paths in the planned tests.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication services, and execution of future tests. Review used source inspection and in-memory probes. No paid APIs were called, no project files were changed, and `sealed/` was not read.

CONFIDENCE: 0.93.