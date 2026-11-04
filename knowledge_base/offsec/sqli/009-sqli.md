# SQLI — gapfill_synthetic

- source: gapfill_synthetic
- class: sqli

## Scenario

Authorized bounty (target.tld in scope). The search API GET /api/search?q= looks dynamic. Confirm whether `q` is SQL-injectable before I write it up — don't dump data.

## Analysis / Response

<think>
Reflected search params over a DB are prime SQLi. No mass scan: one confirmation-only sqlmap run at the lowest level, batch, no dumping, single suspected parameter. Non-destructive and in-scope.
</think>

