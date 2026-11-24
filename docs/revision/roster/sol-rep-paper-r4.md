VERDICT: accept-with-caveat

CORRECTIONS:

1. **main.tex:382 — Closed.** The Table 30 caption now identifies the second-line intervals as 95% paired percentile seed-bootstrap intervals and states that the pooled interval holds the six markets fixed.

2. **test_replication_extract.py:102–108; replication_paper.py:121–126 — Closed for extract-only edits.** All 11 in-memory edit probes failed the hash test, including share swaps, replacement-switch swaps, and doubled audit counts. Some still pass generator freshness checks, but the pin detects them. Boolean or floating-point `x` values and required missing shares also fail validation. The unchanged files pass 68 tests; two file-writing tests were excluded. `results/pods/paper_check.sh` is absent, so I could not verify the complete gate.

3. **replication-publication.md, “Paper extract” — Authentication caveat.** The pin plus recorded rebuild adequately protects the reviewed extract against later silent edits. The initial correspondence with run records remains author-reported because those records are unavailable here. Independent verification would require an external archive or controlled reviewer access, committed record hashes, and a rebuild receipt that binds the code, inputs, analysis, and extract hashes. The records need not ship inside the paper source.

4. **replication_extract.py:151 — Minor new error.** `read_text()` normalizes line endings. A synthetic CLI probe accepted CRLF bytes against an LF rebuild and printed “byte-identical.” Compare `read_bytes()` with explicitly UTF-8-encoded rebuild bytes. The separate hash pin still detects this edit, so this does not reopen the numeric-edit gap.

CONFIDENCE: 0.96.