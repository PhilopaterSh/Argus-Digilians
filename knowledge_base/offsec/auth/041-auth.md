# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2022-44727']
- severity: high
- quality_score: 10

## Scenario

Write a detection plan for CVE-2022-44727.

## Analysis / Response

Detection approach for CVE-2022-44727 in PrestaShop lgcookieslaw:

1) Inventory: find every PrestaShop lgcookieslaw instance and record its version, then compare against the affected range in the advisory.

2) Request-level test for PrestaShop lgcookieslaw (authorized targets only):
 1. Send a GET request to /modules/lgcookieslaw/views/css/front.css on the target; flag it as vulnerable when the expression `status_code == 200` evaluates to true.

3) Log and traffic indicators: look for database error messages or unusually slow responses (time-based probes) from GET /modules/lgcookieslaw/views/css/front.css.

You can automate the CVE-2022-44727 test with Nuclei or any scanner, though it is not required.
