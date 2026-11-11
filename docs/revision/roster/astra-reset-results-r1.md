VERDICT: accept-with-caveat

CORRECTIONS:

1. `docs/revision/posthoc/reset_block.py:141` — Preserve the six expected markets when records are missing. `_complete()` only inspects markets present in the input. Removing an entire market produces `missing: []`, pools five markets, computes four-market leave-one-out values, and can score pooled S as “met”. I reproduced this case. Report the missing cells and withhold affected statistics and scores. Add a whole-market omission test.

2. `docs/revision/posthoc/reset_block.py:52` — Validate gain arrays against seed lists: one-dimensional, finite, equal lengths, unique seed identifiers, and 200 observations for production records. Matching seed lists alone is insufficient. I reproduced acceptance of 199 gains paired with 200 seed identifiers. Add malformed-record tests. The actual 72 input arrays pass these checks; their ordered seeds match, and the 18 base reference pairs and relevant provenance agree.

3. `docs/revision/paper-v2/main.tex:240` — Replace “Replacement … adds” with “The difference between the two prescribed searches … is”. Apply the same terminology to the caption at line 243. State explicitly that I does not identify the optimal value of replacement. The later qualification about different knobs helps but leaves the initial attribution ambiguous.

Rulings 1–3 are acceptable: the separate module preserves the requested analysis, the plan fixes no bootstrap seed, and the reproduced pooled-S scores permit the specified conclusion. Both 9,999-resample analyses, headline values, switches, flags, expectations, table, and all 29 paper values match the saved output exactly. The existing posthoc output and tables are unchanged. Fifteen tests that require no file writes passed; the missing-market and malformed-array cases are not covered.

CONFIDENCE: 0.97