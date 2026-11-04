# CLICKJACKING — gapfill_synthetic

- source: gapfill_synthetic
- class: clickjacking

## Scenario

Response is missing X-Frame-Options and has no CSP frame-ancestors. I framed the page in an iframe. Clickjacking — critical account takeover?

## Analysis / Response

<think>
Framing is possible, but impact depends on whether a sensitive state-changing action is reachable by a framed click at a predictable position. A static marketing page framed = no impact. A one-click 'delete account'/'transfer' with no confirmation = real. 'Critical ATO' is unjustified without demonstrating a specific harmful action a tricked click performs. Missing XFO alone is at most low/informational.
</think>

**Verdict: Downgrade — missing anti-framing headers is Low/Informational without a sensitive action.**

Framability is necessary but not sufficient; severity comes from what a tricked click does.

**Required to substantiate:** identify a state-changing, one-click action with a stable position (e.g. 'Delete account', 'Authorize app') lacking confirmation/re-auth, and a PoC overlay that lands the click.

**As reported** (framing, no specific action): no demonstrated impact.

**Severity:** Low / Informational — ≈4.3 (UI:R, I:L) only if a meaningful action is proven; otherwise Informational.

**Fix:** `X-Frame-Options: DENY` or `Content-Security-Policy: frame-ancestors 'none'`.

**Don't** claim 'critical account takeover' — severity inflation, will be rejected. Show the clickjacked action or report it as a low-severity header gap.
