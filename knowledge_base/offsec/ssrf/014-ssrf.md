# SSRF — gapfill_synthetic

- source: gapfill_synthetic
- class: ssrf

## Scenario

Authorized. Export endpoint POST /api/export takes JSON {"url":"..."} to fetch a remote CSV. I think SSRF — confirm it reaches internal/metadata, non-destructively.

## Analysis / Response

<think>
SSRF confirmation: point url at cloud metadata and see if the body returns. One curl POST. If IMDSv2 is enforced, a plain GET to 169.254.169.254 returns 401 and I must not over-claim. Read status/body carefully.
</think>

