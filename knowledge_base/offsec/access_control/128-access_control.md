# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-862
- cve: ['CVE-2021-22017']
- severity: medium
- quality_score: 13

## Scenario

What should I look for in logs to spot CVE-2021-22017 exploitation?

## Analysis / Response

How to detect CVE-2021-22017 (vCenter Server):

1) Inventory: start from asset inventory, since a version match for vCenter Server is the safest first signal.

2) What the CVE-2021-22017 probe does:
 1. Send a POST request to /analytics/ceip/sdk/..;/..;/..;/analytics/ph/api/dataapp/agent?_c=vSphere.vapi.6_7&_i=9D36C850-1612-4EC4-B8DD-50BA239A25BB on the target with a crafted 354-byte body; a positive result is when the expression `status_code == 201` evaluates to true.
 2. Send a POST request to /analytics/ceip/sdk/..;/..;/..;/analytics/ph/api/dataapp/agent?action=collect&_c=vSphere.vapi.6_7&_i=9D36C850-1612-4EC4-B8DD-50BA239A25BB on the target with a crafted 2065-byte body; the target is likely vulnerable if the response body contains "BUILD" and "VERSION" and "OSTYPE" and the HTTP status is 200.

3) Log and traffic indicators: look for low-privilege or anonymous sessions receiving 200 responses from POST /analytics/ceip/sdk/..;/..;/..;/analytics/ph/api/dataapp/agent?_c=vSphere.vapi.6_7&_i=9D36C850-1612-4EC4-B8DD-50BA239A25BB.

You can automate the CVE-2021-22017 test with Nuclei or any scanner, though it is not required.

**Security Impact:** Broken access control enables unauthorized users to access, modify, or delete resources belonging to other users, potentially leading to data theft, privilege escalation, and regulatory violations.

**Remediation:** Implement role-based access control (RBAC) with server-side enforcement. Deny by default. Validate authorization on every request. Use indirect object references. Implement proper ownership checks. Log access control failures.
