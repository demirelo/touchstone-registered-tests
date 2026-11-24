# Churn replication: commitment publication record (plan section 5)

| Item | Value | Source |
|---|---|---|
| Manifest | `experiments/v2/replication-manifest.json`, sha256 `6f59f245830fb1279c1e98071c2a35ec8833c3becb381430dd7c513175db68c5`, 28 files, code commit `d59e7db3d15a481eee7ef32f12e0a7646ecb6893` | `commitment.py check` passes |
| Manifest commit | `4e9978c983409bea27ebdbc2ebedd14853db9b2f` (signed by the author), parent d59e7db | `git log` |
| Push | `e8ea98b..4e9978c HEAD -> main` on github.com/demirelo/touchstone, by the author | author's terminal output |
| Remote record | GitHub API `repos/demirelo/touchstone/commits/main`: sha 4e9978c, committer date 2026-11-20T16:04:06Z; read 2026-11-20T16:04:41Z | `gh api` |
| Bitcoin tip at publication | height 976752, read 2026-11-20T16:04:41Z | `https://mempool.space/api/blocks/tip/height` |
| OpenTimestamps stamp | `experiments/v2/replication-manifest.json.ots`, submitted 2026-11-20T16:04:57Z to a.pool and b.pool.opentimestamps.org, a.pool.eternitywall.com, ots.btc.catallaxy.com; pending until upgraded | `uvx --from opentimestamps-client ots stamp` |
| Upgraded proof | upgraded 2026-11-20T18:26:16Z; Bitcoin attestations at blocks 976760 (catallaxy calendar) and 976761 (bob calendar); the other calendars still pending | `ots upgrade`, `ots info` |
| Attestation check | merkle roots in the proof match the block headers: 976760 `43bf5084...5a672f` (block `...a6d49fd2`), 976761 `7e423ef5...ae53598` (block `...dc4ae7a3`); read 2026-11-20T18:26:39Z | `https://mempool.space/api/block/<hash>` |
| A (lowest attestation) | **976760** | `ots info` |
| H = A + 144 | **976904**; draw after six confirmations (tip at least 976909) | plan section 5 |

The publication height (976752) is below any possible A, so the commitment was public before H.

## Draw (plan section 5)

| Item | Value | Source |
|---|---|---|
| Draw record | `experiments/v2/replication-draw.json`, sha256 `f16d523942381a9e8165ca7cbca33de9f7905be85f5bbd1d61de51467a532b3b`, status final, written 2026-11-21T13:46:27Z | `.venv/bin/python scripts/block_draw.py --ots experiments/v2/replication-manifest.json.ots --protocol experiments/v2/replication-manifest.json --out experiments/v2/replication-draw.json --poll 300` |
| Block H | 976904, hash `0000000000000000000187abd78f409c52630927b65e12ac57b2906293513cbf`; both explorers agree; tips 976912 at the draw (H + 8) | draw record `answers_at_h`, `tips` |
| Anchor | verified, A = 976760, merkle root `43bf5084...5a672f`; header chain A to the tip kept in the record | draw record `anchor`, `headers` |
| Protocol | `protocol_sha256` 6f59f245...db68c5, equal to the manifest sha256 | draw record |
| Instances check | `draw_v2.instances(draw, manifest, proof, 976752, calibrate=False)`: confirmatory true, salt sha256 `324e48754c60450def1ac9abb7aed84c83c9e92281c11465c213d7b21c18f390`; no calibration on the Mac | local call, 2026-11-21 |

One draw: the script ran once and wrote the record once. No restamp and no redraw.

## Run and analysis

| Item | Value | Source |
|---|---|---|
| Pod 1 | RUN OK, 11.13 USD recorded | ledger `replication-p1` |
| Pod 2 launch p2 | UPLOAD FAILED (bundle) after 96 s, pod deleted (verified); transient: a diagnostic pod then pushed both tarballs (`runpod-v2/upload-diag-2026-11-22.log`) | `rep_p2_launch.log` |
| Pod 2 launch p3 | pod eo8edyb2i8q028, remote 2026-11-22T17:25Z to 2026-11-23T20:30Z (UTC, pod clock); gate0 bit-identical; continue queued 20, ran 21, 0 lost, 0 failed, 0 mismatch; RUN OK; pod deleted (verified, list empty, get 404) | `rep_p3_launch.log`, `logs_rep2_p3/rep.log` |
| Output | `followup3-rep`: 1419 records, 0 bad, 0 not inventoried | launcher `verify` line |
| Analysis | `rep_v2.py --stage analyse` on a clone of the pulled output, Mac, 2026-11-23T20:36Z; counts continued 20, frozen 52, stopped 0, unresolved 0; round-1 mismatch false; gate ok; 0 problems; 0 unscorable | `replication-analysis.json`, sha256 `28da11c0cf9a6485ff1238a53b339d1079e7bc9de3b917d38370551ce718c37f` |
| Expectations, primary winners | 1 met, 2 met, 3 met, 4 met, 5 met | `replication-analysis.json` `primary.expectations` |
| Expectations, all-frozen (sensitivity) | 1 met, 2 met, 3 not met (d at p = 0.03: 4 of 6 markets lower), 4 met, 5 met | `replication-analysis.json` `frozen.expectations` |
| Paper extract | `replication_extract.py --out <analysed clone> --manifest experiments/v2/replication-manifest.json --draw experiments/v2/replication-draw.json --check replication-extract.json` rebuilds the extract from the run records (the analysis is recomputed and must be byte-identical first): ok, byte-identical, 2026-11-24 | `replication-extract.json`, sha256 `36e7c69be53db5c606c2a0ff365c4cae380efe4db081da35fba0eec8a9750cae` (pinned in `test_replication_extract.py`) |
| Extract rebuild receipt | `replication_extract.py` with git blob `09731a5a1d4142e56d1c8c92a5ef50f0b669f5fc` (content hash, which signing does not change), `--check` on the analysed clone: "ok: the extract rebuilt from the run records is byte-identical; records 1426 files, digest 51086341e028c820f2b5a0092639554e5844523a9526aa050862ef245b31efdf" (2026-11-24). The same digest over the pulled pod output `results/pods/rep_p3_out/followup3-rep` (hashing only): 1426 files, `51086341e028c820f2b5a0092639554e5844523a9526aa050862ef245b31efdf`. Inputs: manifest sha256 `6f59f245830fb1279c1e98071c2a35ec8833c3becb381430dd7c513175db68c5`, draw sha256 `f16d523942381a9e8165ca7cbca33de9f7905be85f5bbd1d61de51467a532b3b`, analysis sha256 `28da11c0cf9a6485ff1238a53b339d1079e7bc9de3b917d38370551ce718c37f`, extract sha256 `36e7c69be53db5c606c2a0ff365c4cae380efe4db081da35fba0eec8a9750cae`. The paper gate runs `pytest test_replication_paper.py test_replication_extract.py` in `docs/revision/followup3` (the extract pin) and `replication_paper.py --check`. The run records go into the public replication archive with the release, so a third party can rerun `--check` and match the digest. | this session; `replication-extract.json` |
