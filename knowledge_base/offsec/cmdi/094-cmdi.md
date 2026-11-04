# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2024-1709']
- severity: critical
- quality_score: 14

## Scenario

How do I harden ConnectWise ScreenConnect against CVE-2024-1709?

## Analysis / Response

Remediation for CVE-2024-1709 (ConnectWise ScreenConnect):

1) Patch: Update ConnectWise ScreenConnect to version 23.9.8 or later.

2) Interim mitigation and hardening: Rotate credentials and session secrets for ConnectWise ScreenConnect after patching, in case the bypass was already used. Enforce authentication centrally in ConnectWise ScreenConnect (middleware or filter) rather than per-endpoint.

3) References: https://www.connectwise.com/company/trust/security-bulletins/connectwise-screenconnect-23.9.8, https://github.com/rapid7/metasploit-framework/pull/18870, https://www.bleepingcomputer.com/news/security/connectwise-urges-screenconnect-admins-to-patch-critical-rce-flaw/, https://www.huntress.com/blog/vulnerability-reproduced-immediately-patch-screenconnect-23-9-8

4) Verify by re-running the CVE-2024-1709 check on GET /SetupWizard.aspx/[string]; the indicators should be gone.

**Security Impact:** Command injection enables arbitrary command execution on the server, potentially leading to complete system compromise, data exfiltration, lateral movement, and persistent backdoor installation.
