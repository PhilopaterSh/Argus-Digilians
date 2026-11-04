# REDIRECT — qwen_cve

- source: qwen_cve
- class: redirect
- cwe: CWE-601
- severity: medium
- quality_score: 9

## Scenario

Which features of an app are typical places for open redirect?

## Analysis / Response

Open redirect usually appears in code like this.

Examples include Express `res.redirect(req.query.next)`, PHP `header('Location: ' . $_GET['url'])` and Django `HttpResponseRedirect(request.GET['next'])` without `url_has_allowed_host_and_scheme`. Login flows, logout pages, OAuth callbacks and link trackers are typical places.

Key points (open redirect):
- Protocol-relative // URLs are a common bypass.
- Substring checks on hostnames are trivially bypassed.
- OAuth redirect URIs must be matched exactly.

**Remediation:** Validate redirect targets against an allowlist of permitted URLs/domains. Use indirect references (mapping IDs) instead of direct URLs. Always display a warning page before redirecting to external domains.
