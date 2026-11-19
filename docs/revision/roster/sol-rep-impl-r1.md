VERDICT: reject

CORRECTIONS:

1. `commitment.py:24–60`: Enforce required manifest coverage, including imported helpers, runner-up parameter records, benchmark inputs, and lockfiles. Reject unlisted `--params` inputs (`rep_v2.py:346`). Listed-file verification alone does not establish completeness.

2. `rep_v2.py:103–143`; `rep_pod.sh:71–89`: Bind records to manifest, plan, draw, and driver hashes. Prevent instance/calibration replacement. Pod 2 checks internal hashes but does not establish that its output belongs to the supplied draw. Driver stages do not check Linux.

3. `rep_collect.py:122–129`: Require the first p=0.05 continuation gate regardless of flags. An empty queue skips it; a cost-refused gate dispatches remaining cells and returns success. Enforce gate evidence before dependent stages.

4. `rep_collect.py:100`; `followup2/convergence_v2.py:152–169`: The continuation comparison permits 1e-9 differences. The plan requires identical results.

5. `rep_collect.py:127`: Run the first cell in a child process with atomic saving. Its exceptions escape instead of returning 6; its death can kill the driver. This repeats the Run B lesson.

6. `rep_collect.py:117–122,150–168`: Validate dependencies, seeds, lengths, provenance, doubling records, and continuation status before reuse/scoring. Apply continuation only to flagged cells. Count missing flagged continuations as “not continued.”

7. `replication_analysis.py:51–58,84–90,105`: Require six named markets and matched seed vectors. A synthetic five-market input scored all five expectations “met”; unequal vectors silently truncate.

8. `rep_v2.py:318–331`: Add separate attack/reference terms, efficiency, absolute market intervals, and the specified paired interval outputs. Missing R3 can also crash pooled analysis.

9. `rep_collect.py:163–168`: Compute expectation 5 from primary winners and report frozen sensitivity. Frozen-only diagnostics change the committed expectation.

10. `rep_pod.sh:140,177–190`: Use a shared replication lock and identify pod 1’s exact spend/output. Separate pod locks permit overlapping use of one reservation. Successive pods require distinct launch tags.

11. `rep_pod.sh:215–230,327,360`: Save inventories on failure exits and retry incomplete retrieval before deletion. Current failure paths can delete untransferred output.

12. `rep_v2.py:243–254,295`: Admit churn-search workers and persist reduced limits across restarts. Correct `cost_estimate.py:38–47` gate order, duplicated work, and diagnostics assumptions.

13. Notes rulings: 1 corrected above; 2 arithmetic accepted, estimate provisional; 3 accepted; 4 accepted; 5 rejected; 6 accepted; 7 corrected above; 8 rejected; 9 accepted, retaining publication evidence.

14. Checks: 32 Python tests passed; shell syntax passed. Harness execution was blocked by read-only temporary-directory restrictions.

CONFIDENCE: 0.94.