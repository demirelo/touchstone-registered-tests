VERDICT: reject

CORRECTIONS:

1. **FlashProve cost mapping remains incomplete.** In `outline.md`, section 1 still uses expensive verification to justify a buyer’s sampling budget without the required qualification. Section 10 assigns proving cost to the model’s audit cost “whoever bears it.” However, `paper/main.tex:47` charges audit cost against the operator’s budget. Make this mapping conditional on the operator funding both proving and verification. Provider-funded proving would require separate incentive accounting. Carry this condition and the protocol-versus-fast-code limitation into section 1. [Anthropic’s release](https://www.anthropic.com/research/provable-inference) distinguishes these costs and guarantees.

2. **The noise mapping needs correction.** Section 10 says verification noise would approach zero. The registered model already observes delivered quality exactly during an audit (`paper/main.tex:43–45`); its noise affects delivered quality. Proving execution of an integer model does not remove that noise or establish output quality. Describe proof soundness separately. Keep any alternative quality model explicitly outside the registered evaluations, with all assumptions, metrics, and claims unchanged.

CONFIDENCE: 0.97
