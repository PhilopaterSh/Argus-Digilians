# DESER — qwen_cve

- source: qwen_cve
- class: deser
- cwe: CWE-502
- cve: ['CVE-2025-15375']
- severity: high
- quality_score: 12

## Scenario

Categorize CVE-2025-15375.

## Analysis / Response

CVE-2025-15375 is classified as Insecure Deserialization, based on CWE-502. NVD also lists CWE-20 for it. The CWE-502 mapping for CVE-2025-15375 comes from NVD weakness data rather than keyword guessing. Label CVE-2025-15375 as Insecure Deserialization / CWE-502, severity High.

**Security Impact:** Insecure deserialization can lead to remote code execution, authentication bypass, injection attacks, and privilege escalation by manipulating serialized object data.

**Remediation:** Avoid deserializing untrusted data. Use safe serialization formats (JSON) instead of binary formats. Implement integrity checks (digital signatures) on serialized data. Use class allowlists for deserialization. Monitor deserialization operations.
