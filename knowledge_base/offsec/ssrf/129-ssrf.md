# SSRF — qwen_cve

- source: qwen_cve
- class: ssrf
- cwe: CWE-918
- cve: ['CVE-2021-20346']
- severity: high
- quality_score: 12

## Scenario

How to resolve CVE-2021-20346?

## Analysis / Response

Check the vendor's advisory for CVE-2021-20346 and install the corrected release of Ibm Collaborative Lifecycle Management, since NVD does not record a precise fixed version. Patch or advisory references for CVE-2021-20346: https://exchange.xforce.ibmcloud.com/vulnerabilities/194595; https://www.ibm.com/support/pages/node/6457739. Beyond the fix for CVE-2021-20346, these Server-Side Request Forgery (SSRF) hardening measures help:
- Resolve the host name, validate the resulting IP and connect to that same IP.
- Set short timeouts and size limits on server-side fetches.
- Upgrade the affected component to the release that adds destination validation.
Once CVE-2021-20346 is fixed, confirm the deployed build and check historical access logs for suspicious requests.

**Security Impact:** Server-side request forgery enables an attacker to make requests from the server to internal services, potentially accessing cloud metadata endpoints, internal APIs, and bypassing firewall restrictions.
