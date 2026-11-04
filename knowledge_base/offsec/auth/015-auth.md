# AUTH — gapfill_synthetic

- source: gapfill_synthetic
- class: auth

## Scenario

I can enumerate valid usernames (/login says 'wrong password' for real users, 'no such user' for fake). Also no rate limiting on login. Report as critical?

## Analysis / Response

<think>
Two separate observations. Username enumeration via differential errors is real but low on its own (info disclosure aiding other attacks). No login rate limiting is a weakness but by itself often low/medium and sometimes explicitly OOS. 'Critical' requires chaining into a demonstrated ATO (enumerate + no limit + weak policy → stuffing/brute success shown). Without a demonstrated ATO this isn't critical, and many programs mark both as known/accepted.
</think>

**Verdict: Downgrade & check scope — Low/Medium as reported, not critical.**

**Two findings, each limited alone:**
1. Username enumeration (differential errors): Low ~3.7 (C:L). Aids targeting.
2. No login rate limiting: Low/Medium — impactful only if brute/stuffing success is *demonstrated*.

**To justify higher:** chain them — enumerate a user set, then show a working brute/stuffing login against your own test account. Only a demonstrated ATO warrants High.

**Severity:** Low→Medium as described; High only with a proven ATO chain.

**Fix:** uniform auth error ('invalid username or password'), IP/account rate limiting + backoff, MFA.

**Caution:** many programs list 'no rate limiting' and 'user enumeration' as known/OOS — check policy first or it's a rejected OOS/duplicate.
