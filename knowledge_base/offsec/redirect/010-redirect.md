# REDIRECT — gapfill_synthetic

- source: gapfill_synthetic
- class: redirect

## Scenario

In scope: app.target.tld. I suspect the `next` redirect param on login is unsafe. Confirm with a single request.

## Analysis / Response

<think>
Open-redirect confirmation is one request: send an absolute external URL in `next`, read the Location header, don't follow. Signal: Location pointing to my external host = unvalidated redirect.
</think>

