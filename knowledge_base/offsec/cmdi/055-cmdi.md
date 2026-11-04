# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-502
- cve: ['CVE-2020-9484']
- severity: critical
- quality_score: 12

## Scenario

True or false: CVE-2020-9484 is mapped to CWE-502.

## Analysis / Response

True. CVE-2020-9484 (Apache Tomcat Remote Command Execution) is recorded with CWE-502, consistent with its classification as insecure deserialization.

When using Apache Tomcat versions 10.0.0-M1 to 10.0.0-M4, 9.0.0.M1 to 9.0.34, 8.5.0 to 8.5.54 and 7.0.0 to 7.0.103 if a) an attacker is able to control the contents and name of a file on the server; and b) the server is configured to use the PersistenceManager with a FileStore; and c) the PersistenceManager is configured with sessionAttributeValueClassNameFilter="null" (the default unless a SecurityManager is used) or a sufficiently lax filter to allow the attacker provided object to be deserialized; and d) the attacker knows the relative file path from the storage location used by FileStore to the file the attacker has control over; then, using a specifically crafted request, the attacker will be able to trigger remote code execution via deserialization of the file under their control. Note that all of conditions a) to d) must be true for the attack to succeed.

**Remediation:** Avoid calling OS commands with user input. Use language-native APIs instead of shell commands. If commands are necessary, use strict allowlists for permitted values. Never concatenate user input into command strings. Implement sandboxing.
