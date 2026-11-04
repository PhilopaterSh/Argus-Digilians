# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2021-21799']
- severity: medium
- quality_score: 10

## Scenario

Explain how a scanner checks for CVE-2021-21799.

## Analysis / Response

Checking for CVE-2021-21799 on Advantech R-SeeNet:

1) Inventory: find every Advantech R-SeeNet instance and record its version, then compare against the affected range in the advisory.

2) Request-level test for Advantech R-SeeNet (authorized targets only):
 1. Send a GET request to /php/telnet_form.php?hostname=%3C%2Ftitle%3E%3Cscript%3Ealert%28document.domain%29%3C%2Fscript%3E%3Ctitle%3E on the target; the target is likely vulnerable if the response body contains "<title>Telnet </title><script>alert(document.domain)</script><title></title>" and the response headers contains "text/html" and the HTTP status is 200.

3) Log and traffic indicators: look for query strings or form fields sent to GET /php/telnet_form.php?hostname=%3C%2Ftitle%3E%3Cscript%3Ealert%28document.domain%29%3C%2Fscript%3E%3Ctitle%3E that contain HTML tags or event-handler attributes.

Only run active checks for CVE-2021-21799 against systems you own or are authorized to test.
