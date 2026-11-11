VERDICT: reject

CORRECTIONS:

1. **None — plan §§3, 4, 8.3; `reset_followup_v2.py:383`, `:461`.** The round-6 corrections are closed. Objective differences now prevent `identical`. Both saved reproduction gates pass the current comparators. Their records contain provenance and dependency hashes. All three inventories match their files. Headline diagnostics cover three rules and nine policies on 200 seeds; D2 reset counts are zero. The 168 bundled records match their sources.

2. **None — plan §§3, 7, 8.4; `results/pods/reset_pod.sh:22`, `:66`, `:73`.** The launcher checks frozen tracked code, requires `--require-identical` before the 18 cells, uses the correct stage order, assigns 16 search workers and 10 evaluation workers by default, and requires 28 GiB memory.

3. **Plan §7; `results/pods/reset_pod.sh:90`; `results/pods/runpod.py:32`.** Make SSH failures return a nonzero process status. The helper currently prints the remote failure and exits successfully; an isolated check confirmed this for SSH exit 255. The launcher can therefore mark STOP as delivered when delivery failed. Check the cap deadline on the pod before each stage.

4. **Plan §7; `results/pods/reset_pod.sh:89`, `:30`.** Enforce the 1.3× hard stop before retrieval. Currently, reaching that threshold starts cleanup, which permits up to 25 minutes of pulls before deletion. Monitoring also starts after preparation and polls every 120 seconds. Use a deadline guard that covers preparation, execution, and cleanup.

5. **Plan §8.4; `results/pods/reset_pod.sh:30`, `:56`.** Verify retrieved records against their inventories before normal deletion. Pull results are suppressed and unchecked, so `RUN OK` can accompany lost outputs. Also verify deletion of unreachable pods before clearing their IDs; otherwise a failed deletion can leave a billed pod outside cleanup.

6. **Plan §§8.1, 8.3; `results/pods/reset_code.tgz`.** Rebuild and validate the exact launch archive. Its driver matches commit 8d18de4 and lacks d865329’s `copy_inputs` correction.

CONFIDENCE: 0.98.