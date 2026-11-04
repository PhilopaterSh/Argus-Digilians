# AUTH — gapfill_synthetic

- source: gapfill_synthetic
- class: auth

## Scenario

A password reset emails a 6-digit code valid 15 min, submitted to POST /reset/verify. No lockout on 20 tries. Finding? How bad?

## Analysis / Response

<think>
6 digits = 10^6, but the 15-min window and throttle change the math. At 100 req/s, 10^6 ≈ 2.7h > 15 min, so single-code brute may not finish — UNLESS codes aren't invalidated, I can request many, or I parallelize. Key tests: is there ANY throttle; does requesting a new code invalidate old ones/widen the window; is the code account-bound. Must show feasibility, not assert it. If feasible → account takeover.
</think>

**Broken auth — no rate limiting on reset-code verification (brute-forceable).**

**PoC (feasibility-demonstrating, on your own test account):**
```
for c in $(seq -w 0 999999); do
 curl -s -o /dev/null -w "%{http_code}\n" -X POST target.tld/reset/verify -d "email=victim@test&code=$c"
done | grep -m1 200
```
With no lockout and ~200 concurrent req/s the keyspace is searchable; prove it end-to-end on your test account.

**Root cause:** no per-account/IP throttle, no lockout, codes not invalidated after N failures.

**Impact:** account takeover of any user by email.

**Severity:** High — AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N ≈ 8.1, conditioned on demonstrated feasibility.

**Fix:** exponential backoff + hard lockout (5/code), invalidate on threshold, ≥8 alphanumeric entropy, bind code to session.
**Edge case:** if an upstream WAF silently throttles ~50/s, the attack may be infeasible — measure achievable throughput before rating High.
