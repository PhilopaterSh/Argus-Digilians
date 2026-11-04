# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2020-12259']
- severity: medium
- quality_score: 9

## Scenario

How do I confirm CVE-2020-12259 without a scanner?

## Analysis / Response

Checking for CVE-2020-12259 on rConfig:

1) Inventory: start from asset inventory, since a version match for rConfig is the safest first signal.

2) What the CVE-2020-12259 probe does:
 1. Send a GET request to /login.php on the target; it is a hit if the expression `status_code_3 == 200` evaluates to true.

3) Log and traffic indicators: look for query strings or form fields sent to GET /login.php that contain HTML tags or event-handler attributes.

If you use Nuclei, its CVE-2020-12259 template performs the same request and match; otherwise script it yourself.
