# Paper revision after external review round 5: internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Read `docs/revision/roster/brief-paper-ext5-r1.md` for the inputs. Round 1: Sol reject (4) and Astra reject (4), `docs/revision/roster/{sol,astra}-paper-ext5-r1.md`. Commits 1d9c1ad, 9a53432, ecced97 apply every correction:
- Training gains of the lottery reconstructed from the search archives (`posthoc_v2.py`: `train_gain_w0`, `train_gain_profit`, `train_mix`, tested); Table 11 prints them; section 9 says three mixtures meet the W1 training constraint and C*'s public-family mixture (-0.000580) does not, so for C* the drop at the selected weight needs H4; the letter corrects the false claim.
- The audit recomputes Q1 categories with the frozen `q1_family` (tested); section 8 and the letter claim only categories, direction rejections and Q4 decisions; the letter says the raw Q1 values are in `audit.json` and that intervals and efficiency labels are not rechecked.
- The fresh1 diagnosis separates the observed count (506 of 9,999 frozen resamples, 5.1 percent) from the probability (4.9 percent), gives the largest rounding residual (1.2e-13), and says "above rounding scale" (tested).
- B3: "positive estimated gain" (Table 11 row and caption).
PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf10/main.pdf` (26 pages, no overfull boxes). The paper gate passes; the letter's table numbers check against the compiled aux.

Check: (1) each round-1 correction is resolved; (2) the round-1 checklist on the current text and letter; (3) new errors.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
