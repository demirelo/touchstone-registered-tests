VERDICT: accept-with-caveat

CORRECTIONS:

1. **main.tex:382 — Closed.** Table 30 now identifies the second-line intervals, confidence level, resample count, seed, and pooled interval over fixed markets. The caption agrees with the analysis code.

2. **test_replication_extract.py — Closed for extract-only edits.** In-memory probes doubled audit counts, swapped shares, swapped x, changed an in-range share, set x=True, and removed a required share. All six failed the unchanged pin test. The first three still pass the generator’s freshness check, but the pin catches them. The new validation rejects Boolean x and missing required shares. Sixty-eight read-only tests passed; two tests that use temporary files were excluded.

3. **replication-publication.md; test_replication_extract.py — Authentication caveat.** The recorded rebuild plus the fixed hash adequately guards against later extract-only edits, provided the recorded rebuild is trusted. It does not independently prove correspondence with unavailable records or enforce a rebuild before someone changes the pin. For independent verification, retain the records in an external archive, publish their inventory hashes and extraction-code revision, and provide reviewer access with a reproducible rebuild receipt. Records need not accompany the paper source.

4. **replication_extract.py — Minor new precision error.** `--check` compares `read_text()` output while reporting “byte-identical.” Text reads normalize line endings, so different bytes can compare equal. Compare `read_bytes()` with the generated UTF-8 bytes; apply the same correction to the analysis comparison. The fixed SHA-256 pin still detects such extract changes.

5. **results/pods/paper_check.sh — Verification limit.** The gate script is absent from this checkout. I verified the pin test directly, but could not confirm its gate integration or repeat the source-record rebuild.

CONFIDENCE: 0.95.