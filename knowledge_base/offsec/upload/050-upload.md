# UPLOAD — qwen_cve

- source: qwen_cve
- class: upload
- cwe: CWE-434
- cve: ['CVE-2025-52691']
- severity: high
- quality_score: 14

## Scenario

How do I harden SmarterMail against CVE-2025-52691?

## Analysis / Response

How to remediate CVE-2025-52691:

1) Patch: The source data does not name a fixed release of SmarterMail; check the vendor advisory below for the patched version and apply it.

2) Hardening: Disable script execution in SmarterMail upload directories at the web-server level. Store uploads for SmarterMail outside the web root and serve them with a non-executable content type.

3) References: https://www.csa.gov.sg/alerts-and-advisories/alerts/al-2025-124/, https://github.com/watchtowrlabs/watchTowr-vs-SmarterMail-CVE-2025-52691, https://github.com/watchtowrlabs/watchTowr-vs-SmarterMail-CVE-2025-52691?ref=labs.watchtowr.com, https://www.cisa.gov/known-exploited-vulnerabilities-catalog?field_cve=CVE-2025-52691

4) Verify by re-running the CVE-2025-52691 check on POST /api/upload; the indicators should be gone.

**Security Impact:** Unrestricted file upload allows attackers to upload malicious files such as web shells, enabling remote code execution, defacement, and persistent server access.
