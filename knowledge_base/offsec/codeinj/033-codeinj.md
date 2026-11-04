# CODEINJ — qwen_cve

- source: qwen_cve
- class: codeinj
- cwe: CWE-94
- cve: ['CVE-2022-22947']
- severity: critical
- quality_score: 13

## Scenario

Our SOC wants to monitor for CVE-2022-22947. What should they watch?

## Analysis / Response

Checking for CVE-2022-22947 on Spring Cloud Gateway Code Injection:

1) Inventory: start from asset inventory, since a version match for Spring Cloud Gateway Code Injection is the safest first signal.

2) Reproducing the CVE-2022-22947 check on a test instance:
 1. Send a POST request to /actuator/gateway/routes/[randstr] on the target with a crafted 379-byte body; flag it as vulnerable when the response headers contains "/routes/[randstr]" and the out-of-band interaction log contains "dns" and the HTTP status is 201.

3) Log and traffic indicators: look for requests to POST /actuator/gateway/routes/[randstr] containing shell metacharacters such as ;, |, `, $( or encoded equivalents.

Nuclei can automate the CVE-2022-22947 check, but curl or Burp work just as well using the steps above.

**Security Impact:** Code injection allows execution of arbitrary code within the application context, potentially leading to data access, privilege escalation, and complete application compromise.

**Remediation:** Never use eval() or dynamic code execution with user input. Use parameterized APIs. Implement strict input validation. Deploy runtime protection (RASP). Use sandboxed execution environments for dynamic code.
