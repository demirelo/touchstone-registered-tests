# Plain-language summary

A buyer of computing work, such as AI model answers, can afford to check only some of the jobs it receives. A provider
caught cheating is banned, but if new accounts are free, it comes back at once under a new name and the ban costs it
nothing. We tested a simple rule: check new accounts first, then keep checking the newest ones.

In two simulation tests, we fixed the questions, pass rules and analysis in advance. The six test markets were then drawn
from a future Bitcoin block, so nobody could pick favourable cases. Against random checks, the rule cut the cheater's
gain on every one of the 6 markets. The stricter pass-or-fail test passed on only 3 of the 6, each with a caveat about
how thorough the attack search was. The rule did about as well as a rule that trusts accounts with a verified history.

Follow-up runs suggest that the rule's edge comes mostly from catching cheaters who return under new names, and that it
fades when honest providers also come and go. Honest newcomers then take up the checks: the share of the cheater's jobs
that got checked fell from 36.6% to 4.2% as honest turnover rose from 1% to 5% of providers per round. A second run on
six new markets, planned before they were drawn, met all 5 of its expectations, but most of its results by market are
not firm.

The practical lesson: checking newcomers is cheap and helps when honest accounts are stable; when many honest providers
join and leave, a rule based on verified history is the safer choice. The study covers one simulated market design with
fixed settings. Every result, including the failures, is public with the code and records.
