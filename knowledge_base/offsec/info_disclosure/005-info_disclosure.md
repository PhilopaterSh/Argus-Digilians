# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2021-26598']
- severity: medium
- quality_score: 9

## Scenario

How can I detect CVE-2021-26598?

## Analysis / Response

Checking for CVE-2021-26598 on ImpressCMS:

1) Inventory: find every ImpressCMS instance and record its version, then compare against the affected range in the advisory.

2) Active test against a lab copy of ImpressCMS:
 1. Send a GET request to /misc.php?action=showpopups&type=friend on the target; flag it as vulnerable when the body 2 contains "last_login" and "user_regdate" and "uname" and the HTTP status is 200.

3) Log and traffic indicators: look for administrative actions in ImpressCMS attributed to sessions that never authenticated.

A scanner such as Nuclei has a public template for CVE-2021-26598, but the steps above work with curl or any HTTP client.
