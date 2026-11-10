VERDICT: reject

CORRECTIONS:

1. `main.tex:76`; `docs/paper/fable52-triage.md`, item 5 and simulations item 3: “attacker gains were not recorded” is false. All twelve configurations have gains in `experiments/v2/log/Cstar__*__inner.json`, under `detail`; both rechecks also retain them. These records confirm efficiency controlled selection. Report the gains now. In full-budget rechecks, C-thr(12) has lower D2+H3 gain than C*: 0.0761 versus 0.0966 on headline; 0.0178 versus 0.0381 on dev0. Retrieving these values requires no simulation.

2. `main.tex:22,63,331`: Limit “honest providers never replace” to the fixed honest opponents. Initial honest identities are also new, attackers need not replace, and truthful focal policies can replace after false failures. Age identifies replacement history, not dishonesty “almost perfectly.” State that population churn remains untested.

3. `main.tex:21,38,191`: Replace “neither … extends” and “not for the neighbourhood” with “this diagnostic does not establish … for the neighbourhood.” Failure to establish generalisation does not establish its absence. Keep this qualification specific to D2+H3: the exploratory X7-SC interval is positive and inside ±0.05.

4. `main.tex:93`: Replace “age groups are served newest first” with “jobs are audited by age group, newest first.” Add that identities can age out while offering but receiving no jobs. Fable’s ambiguity remains after defining age.

5. `docs/paper/fable52-triage.md`, item 8: “every knob 0” is false. The D2+H3 W1 winner has `x=1`; X7-SC also has nonzero reset controls. Describe truthful delivery with replacement after failures, not a null policy. The zero-gain and no-profitable-candidate findings hold.

6. `main.tex:20–22,257`; triage item 8: The abstract remains overloaded, and the mixture discussion still spans many sentences and tables. Shorten both; the claimed reduction to one sentence did not occur.

No numerical corrections: the new intervals, 10/12 count, envelope differences, 21/98 flags, relative difference, and P|G=1 reproduce. The margin-timing rebuttal is valid: `2a288f5` predates `c5227a0`.

CONFIDENCE: 0.98.