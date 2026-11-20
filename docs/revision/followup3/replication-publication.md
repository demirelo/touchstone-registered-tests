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
