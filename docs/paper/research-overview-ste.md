# Touchstone: the research and modeling work, in plain language (ASD-STE100 style)

## 1. The problem

A compute market sells work. Buyers send jobs. Providers do the jobs and get payment.

The buyer cannot see the quality of the work. The buyer can only check a small sample of jobs. A check is called an audit. Each audit costs money, so the budget for audits is small.

A provider can cheat in two ways:

- It can do less work than it claims (it "shades" its effort).
- It can claim a higher quality than it delivers (it "inflates" its claim).

The market has only weak punishments:

- It can return the payment of a failed job to the buyer (a refund).
- It can stop the provider for some rounds (a ban).
- It cannot take a deposit or an entry fee before the provider earns money.

The hardest problem is the reset. A banned provider can stop using its old name and start again with a new name at no cost. Then the ban has no effect.

Our question: can a market rule make cheating unprofitable when audits are few, punishments are small, and a reset is free?

## 2. The model (the simulator)

We built a simulator of this market. It runs in rounds.

- There are 10 providers. Each provider has a maximum quality, a cost per job, and a capacity of 6 jobs per round.
- In each round, 50 jobs arrive. Each job has a value for the buyer.
- A market rule assigns jobs to providers, sets payments, selects jobs to audit, and applies refunds and bans.
- An audit measures the delivered quality with random noise. A job fails when the measured quality is lower than the claim minus a tolerance.
- One episode has 200 rounds.

We measure two things:

- **Gain.** The extra profit that a cheating provider gets, compared with its best honest behavior. We divide this extra profit by one provider's share of the best possible total value (the "fair share").
- **Efficiency.** The total value that the market creates, compared with the best possible value.

## 3. The market rules

We compare four rules.

- **B1.** Fixed prices by quality tier. No audits.
- **B2.** Fixed prices by quality tier. Random audits.
- **B3.** An auction (the job goes to the best score, the payment is set by the second-best score). Random audits.
- **R3.** Our proposed rule. It uses the B3 auction, and it audits in a different way:
  - It audits **the jobs of new providers first**. A provider is "new" during its first 10 rounds. It audits all of these jobs when it has enough audits in that round.
  - It spends the remaining audits half on the newest providers and half at random.
  - It keeps a reserve of audits for the last 10 rounds and audits every job then.

The idea: a reset makes a provider new. A new provider gets audited on every job. So a reset no longer gives a clean start. It gives a period of full checks. We call this "audit dues": the new name pays with checks, not with money.

## 4. The attackers

A rule is only as good as the best attack against it. We used several kinds of attackers.

- **Searched attackers.** These are cheating strategies with adjustable settings. A search program (CMA-ES) tries thousands of settings and keeps the most profitable one. Family D2 adapts its cheating after each audit. Family D2+H3 also resets its name after a failed audit.
- **A sealed attacker (H2).** A separate session wrote an attacker family before we designed our rule. We did not read it until the final test. So we could not tune our rule against it.
- **A language-model attacker (H1).** A large language model played the provider and tried to make money. This test was exploratory.
- **Six new attackers** after the final test (exploratory). For example, an attacker that waits until it is no longer new and then cheats, and a group of providers that reset at the same time.

For each attacker, we also built an honest "twin". The twin uses the same strategy but never claims more than it delivers. We compare the attacker with the best honest reference. This shows how much of the profit comes from cheating.

## 5. The research process: decide first, test later

We fixed the rules of the study before we built our rule. This makes it harder to change the test to get a good result. It does not make it impossible: we made four changes later, and we report each one.

1. **Lock (17 October 2026).** We wrote down the claim, the thresholds, the attackers, the seeds, and the statistics. We signed this state and time-stamped it on the Bitcoin blockchain (OpenTimestamps).
2. **Amendments.** When we had to change something, we wrote an amendment, signed it, and time-stamped it before the change. There were four amendments:
   - Amendment 1 added a second claim about the reset attack.
   - Amendment 2 defined how we design and tune our rule.
   - Amendment 3 replaced our first rule after it failed a test that we had written in advance. The new rule (R3) added "new providers first".
   - Amendment 4 raised the cost limit for the language-model test by 30 USD.
3. **Falsification tests first.** Before the final test, we ran five tests that could stop our rule. The first version of our rule failed one test. We reported this and stopped that version.
4. **Freeze (18 October 2026).** We fixed our rule and its settings.
5. **Unseal and final test.** We opened the sealed attacker and tested on 40 new random seeds that we had never used.

Independent AI reviewers (Sol and Astra, two other models) checked every plan, every amendment, and every result. Many times they rejected our first version. We corrected it and asked again.

## 6. The registered results

- **The original claim failed.** Against the sealed attacker, R3 was safe: its efficiency was at least 0.994 and the attacker's gain at most 0.044. But the claim also required R3 to beat B2 and B3 by a margin. It did not. Against this attacker, B2 and B3 were already safe. We had predicted this failure in Amendment 1.
- **The amended claim passed.** Against the reset attack, the cheater's gain was 0.57 of a fair share under B2, 0.35 under B3, and 0.07 under R3. R3's efficiency was at least 0.998. One limit: the statistical method for this claim was checked on development data with B3 in place of R3, so its error rate for R3 is not proven.
- **The language-model attacker** made money only against B1 (no audits). Against R3, the result is "inconclusive" by our own rules. This test was exploratory.

## 7. The theory

We proved why the result happens. The main parts:

- **Uniform audits cannot use the ban.** If audits do not depend on the age of a name, and a reset is free, a cheater resets after each failure. The ban then costs nothing. Only the refund remains, and a refund alone is too small.
- **New providers are fully covered.** R3 audits every job of a new provider while it has enough audits. If too many new providers come at the same time, some jobs escape. We calculated the escape probability.
- **A reset name stays a target.** After its first 10 rounds, a reset provider is still the newest established name. R3 audits about 92 to 100 percent of its jobs. So a reset gives no quiet period.
- **A bound on profit.** We proved an upper limit for the long-run profit of a "cheat and reset" plan. The limit shrinks with the ban length and with the chance of detection.
- **Small cheating is always possible.** The tolerance lets a provider cheat a little with almost no risk. No rule in our class can stop this. So we claim "small gain", not "no gain".

We checked the theory in 72 fixed test cases. Where the conditions of the theory held, it agreed with the simulator. The theory does not cover the adaptive reset attacker or groups of providers.

## 8. The robustness tests

We wrote 292 test cases and our predictions before we ran them. We changed one thing at a time: the audit budget, the audit cost, the market size, the number of jobs, the noise, an entry fee, the length of an episode, and the position of the provider.

- In many cases, R3 kept its advantage against the reset attack. These tests reused development seeds, so they are exploratory.
- **Failure 1: expensive audits.** When an audit costs as much as the profit of one job, the reserve for the last rounds uses the full budget. R3 then audits nothing before the last 10 rounds, and cheating becomes easy. This is a design defect. A limit on the reserve can probably fix it (we did not test this).
- **Failure 2: groups of new providers.** When five cheaters work together, their new names exceed the audits for new providers. The cheater's gain under R3 rose to 0.31. The data do not show that the same reset time is the cause.
- **Failure 3: high noise.** With very noisy audits, honest providers fail checks too, and the efficiency of every audited rule drops.
- Some predictions were wrong. We report all of them.

## 9. What we can claim

- Under free resets, uniform random audits fail, and auditing new names first works much better. This holds in many market settings.
- The method is a contribution of its own: we locked the protocol before we built our rule, sealed an attacker, time-stamped every step, and reported our failures and changes.
- A related older study (Sarmenta, 2001) also checked new volunteers more and considered name changes. Our work differs in its market, its payments, its audit budget, its searched attackers, and its locked evaluation.
- We do not claim exact protection, an equilibrium, or protection against groups of providers.

## 10. What is next

We write the paper. We check every reference against its original source. Then hostile reviewers read the draft before we submit it.
