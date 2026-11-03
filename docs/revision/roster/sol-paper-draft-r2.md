VERDICT: accept-with-caveat

CORRECTIONS:

1. **Section 8 — Add the Holm reference and cite it at first use.** Disposition (b) is acceptable as a disclosed draft limitation, but it does not close Sol 11/Astra 10. An accessible [original paper](https://sci2s.ugr.es/keel/pdf/specific/articulo/0052_001.pdf) verifies Sture Holm, “A Simple Sequentially Rejective Multiple Test Procedure,” *Scandinavian Journal of Statistics* 6 (1979), 65–70. The method remains uncited at `docs/revision/paper-v2/main.tex:173–174`; `refs.bib` has no Holm entry.

2. **Section 2, bibliography — Complete the remaining identifier fields.** Add DOI or URL fields to `blocki2013audit`, `carlini2019evaluating`, and `vlasiou2014renewal` at `docs/revision/paper-v2/refs.bib:10,12,13`. Sol 11/Astra 10 and `outline.md:104` require an identifier on every entry. The arXiv numbers currently appear only as text. Verified destinations include [IJCAI proceedings](https://www.ijcai.org/Proceedings/2013/), [Carlini’s paper](https://arxiv.org/abs/1902.06705), and [Vlasiou’s paper](https://arxiv.org/abs/1404.5601).

3. **Section 6 — Complete market coverage in the family table.** Keep “both tests,” but specify second-test coverage: D2 runs at the headline market only; D2+H3 and X5-AG/v2 run at the headline and six fresh markets. Update `docs/revision/paper-v2/main.tex:116–120`. Astra 4 remains partly unresolved: “both tests” and “second test” identify evaluations, not markets. The registered coverage follows `experiments/revision-v2-manifest.yaml:5–6,22`.

All other round-1 requests are resolved. Disposition (a) is acceptable on the supplied appendix quotation: the p. 18 forward-pass statement need not be replaced by the separate p. 17 vLLM measurements. Publication height 974379 is acceptable with the supplied provenance. I found no additional substantive errors. I could not complete the knob-count test because an imported library requires a writable cache; the inspected source definitions support the listed counts.

CONFIDENCE: 0.94
