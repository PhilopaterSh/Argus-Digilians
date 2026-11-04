# SSRF — qwen_cve

- source: qwen_cve
- class: ssrf
- cwe: CWE-918
- cve: ['CVE-2021-22255']
- severity: high
- quality_score: 11

## Scenario

How do we close CVE-2021-22255?

## Analysis / Response

Upgrade to a release that fixes CVE-2021-22255; the affected range ends before baserow 1.1.0, so moving to that version or later removes the flaw. Patch or advisory references for CVE-2021-22255: https://baserow.io/blog/march-2021-release-of-baserow; https://gitlab.com/bramw/baserow/-/issues/370. Beyond the fix for CVE-2021-22255, these Server-Side Request Forgery (SSRF) hardening measures help:
- Allow-list destination hosts and schemes rather than block-listing internal ranges.
- Disable redirects in the HTTP client or re-validate each redirect target.
- Resolve the host name, validate the resulting IP and connect to that same IP.
Once CVE-2021-22255 is fixed, confirm the deployed build and check historical access logs for suspicious requests.
