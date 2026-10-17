VERDICT: accept-with-caveat

REASON: The draft preserves the original predicate and reports the amendment separately. It correctly identifies H3 as a known family, makes endpoint admission conditional, and states the limits of proxy validation. However, two parts of the proposed rule need clarification before registration. This vote covers the draft only; the sealed bundle remains unread.

OBJECTIONS:

1. **Issue:** The terminal audit schedule specifies L = 10, but tuning includes L = 3 and L = 20.  
   **Effect:** The reserve and earlier audit quotas are not fully specified for all configurations. Different implementations could change budget compliance and performance.  
   **Checkable support:** Section 4 fixes “500 audits reserved” and “21.05%” earlier coverage, then registers three values of L.  
   **Resolution:** Register the reserve calculation, integer quota calculation, and treatment of unused reserve for every L before tuning.

2. **Issue:** T2 requires a served-job count, but the policy-memory list includes only first-observed rounds and audit counts per identity.  
   **Effect:** The selection rule and its permitted state do not agree. The denominator’s update time can also change audit selection.  
   **Checkable support:** Section 4 defines T2 as “fewest audits per served job,” while its policy-memory list omits served-job counts.  
   **Resolution:** Add these counts to permitted memory and specify when both counts update.

EDITS:

Replace the parenthetical beginning “L = 10” with:

> “The amendment specifies the terminal reserve, cumulative integer quotas, and treatment of unused reserve for each L in {3, 10, 20}. The figures of 500 reserved audits and 21.05% earlier coverage apply only to L = 10.”

Replace “first-observed round and audit counts per opaque identity” with:

> “first-observed round, audit counts, and served-job counts per opaque identity; the amendment specifies each count’s update time and whether the current round’s served jobs enter T2’s denominator before audit selection”

CONFIDENCE: 0.88
