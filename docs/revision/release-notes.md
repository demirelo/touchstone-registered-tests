Second registered test of Touchstone (protocol v2, signed tag `protocol-v2`, OpenTimestamps proof attested in Bitcoin).

The artifact `touchstone-v2.tar.gz` holds all evaluation records of the second test, the draw record with block headers, the instances, the H4 decision and the released H4 bundle, the report with its addendum and the deviation evidence, the promoted inputs, the protocol and its proof, the paper sources, and `uv.lock`, with a manifest of SHA-256 hashes.

Reproduce the report on a clean clone:

    uv run python docs/revision/deviation/reproduce_deviation.py --artifact touchstone-v2.tar.gz --repo https://github.com/demirelo/touchstone-registered-tests

It checks the artifact against the signed tag, checks that the substituted fresh-market configurations differ from the registered ones by at most one unit in the last place (the disclosed deviation), and runs the tagged report's check. Exit 0 means the report is reproduced.

Artifact SHA-256: f6cf682bda2fa5883ff35de00bea2228f2ee8e0c7f2b91168532968fec10812c
