# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-77
- cve: ['CVE-2023-20889']
- severity: critical
- quality_score: 14

## Scenario

What is CVE-2023-20889?

## Analysis / Response

CVE-2023-20889 is a remote code execution vulnerability in VMware Aria Operations for Networks.

Aria Operations for Networks contains an information disclosure vulnerability. A malicious actor with network access to VMware Aria Operations for Networks may be able to perform a command injection attack resulting in information disclosure. It maps to CWE-77.

Root cause: VMware Aria Operations for Networks passes attacker-influenced data into a shell command, interpreter or code-evaluation function.

Scored 7.5 under CVSS v3, CVE-2023-20889 sits in the high band.

Impact: Successful exploitation of this vulnerability can result in unauthorized access to sensitive information.

**Remediation:** Avoid calling OS commands with user input. Use language-native APIs instead of shell commands. If commands are necessary, use strict allowlists for permitted values. Never concatenate user input into command strings. Implement sandboxing.
