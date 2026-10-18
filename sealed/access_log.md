# Access log of the sealed bundle

All times are local (2026-10-17). Actor: the custodian session (separate AI session of spec section 6.1), working in the clone /Users/oemer.demirel/touchstone-custodian at commit d6ee8b6.

| When | Who | Action | Files |
|---|---|---|---|
| 2026-10-17 | custodian | Created the directory `sealed/` and `sealed/h2/` outside both repositories. | (directories) |
| 2026-10-17 | custodian | Wrote the H2 family and checked, outside the bundle, that `embed_d2` reproduces D2 exactly, that the honest point gives honest-max, and that the twin never claims above effort. | `h2/family.py` |
| 2026-10-17 | custodian | Wrote the H1 prompt and the containment statement. | `h1_prompt.txt`, `h2/containment.md` |
| 2026-10-17 | custodian | Generated the final-eval seeds (`secrets`) and the identity salt (`os.urandom`). | `final_eval_seeds.json`, `identity_salt.hex` |
| 2026-10-17 | custodian | Wrote the README. | `README.md` |
| 2026-10-17 | custodian | Ran the section 4 checks (B1, fake backend, smoke) from the clone with TOUCHSTONE_SEALED_DIR set; all four commands passed. Wrote the results. | `b1_check.json` |
| 2026-10-17 | custodian | Computed the commitment (`sim.sealed.bundle_hash`) and the salt hash; checked `verify_bundle` (accepted) and `stray_files` (empty). The seven bundle files are frozen from here on. | (read only) |
| 2026-10-18 | author (assistant session) | Unseal: after the freeze tag freeze-2026-10-18 the author copied the bundle into the repository; bundle hash and salt hash verified against the lock; stray files none; the final evaluation starts. | (read) |
