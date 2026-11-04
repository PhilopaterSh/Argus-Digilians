# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-862
- cve: ['CVE-2024-23055']
- severity: medium
- quality_score: 9

## Scenario

What are the indicators of CVE-2024-23055?

## Analysis / Response

Detection approach for CVE-2024-23055 in Plone Docker:

1) Inventory: find every Plone Docker instance and record its version, then compare against the affected range in the advisory.

2) Active test against a lab copy of Plone Docker:
 1. Send a GET request to / on the target; a positive result is when the response body contains "[randstr].tld" and "PORTAL_URL" and the response headers contains "text/html" and the HTTP status is 200.

3) Log and traffic indicators: look for query strings or form fields sent to GET / that contain HTML tags or event-handler attributes.

If you use Nuclei, its CVE-2024-23055 template performs the same request and match; otherwise script it yourself.
