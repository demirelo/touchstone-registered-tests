VERDICT: accept-with-caveat

CORRECTIONS:
1. `main.tex:191`: Replace “receives more refunds” with “loses more receipts through refunds.” `sim/ledger.py:58–60` deducts refunds from provider receipts.
2. `main.tex:191`: Qualify “the operator pays for the extra audits.” The diagnostic shows more audits of the replacement provider. It does not establish higher total audit spending; targeted audits can displace other audits within the fixed budget.
3. `main.tex:189`: Remove `tab:ph-honest` from the list of exploratory analyses. Its profile was registered, as the paragraph and table caption correctly state.
4. `main.tex:206`; `docs/paper/response-to-review-r9.md:21`: Replace “unrounded” with “computed from full-precision report values; displayed rounded.” The table rounds audited shares to three decimals and scaled profit/refund values to two decimals.

CONFIDENCE: 0.96