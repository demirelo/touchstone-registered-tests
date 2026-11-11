VERDICT: reject

CORRECTIONS:
1. `podctl.py:169`: Balance credits invalidate “never understate.” Offline reproduction: starting balance $10, usage $1, credit $5 produces recorded spend −$4. Include credits in the calculation, or require verified absence of credits throughout the measurement period. Clamping negative results does not fix this.
2. `podctl.py:181,206,208-209`: The watchdog uses wall time for settling and passes that clock into deletion. A simulated forward clock change ended the required 1800-second settle after 30 elapsed seconds. Use a separate monotonic clock for both elapsed budgets. Sol 9 remains partly open.
3. `reset_pod.sh:141,164-165`: Preparation and remote-start failures remain masked. Offline checks returned success after unpack/sync failures and after failures in the background-start command structure. Propagate each preparation failure and require confirmation from the remote process before setting `started=1`. Astra 8 remains partly open.
4. `reset_pod.sh:55-56`; `podctl.py:210-212`: The watchdog releases the launch lock before spend becomes recordable. A same-name relaunch then replaces `.bal0` and removes `.wdend`, losing the previous measurement. Preserve immutable records for each launch and prevent spend reads from mixing launches.
5. `reset_pod.sh:56,116`: Balance and pending-marker writes have unchecked exit statuses. A failed write can permit creation without a persisted baseline or pending marker. Abort before dispatch unless both required writes succeed.
6. `test_reset_pod_harness.sh:90,98-108`: Most terminal-state checks remain substring matches; several scenarios omit them. Require complete expected terminal lines where applicable. Sol 8 remains partly open. Keep launch blocked until the corrected full harness reports HARNESS OK; the reported smoke run does not meet that gate.
7. `podctl.py:169`: Rounding before `ceil` can round downward. Offline reproduction: $0.010000001 becomes $0.01 instead of $0.02. Use decimal arithmetic with upward cent rounding.

CONFIDENCE: 0.98.