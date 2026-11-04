# DESER — qwen_cve

- source: qwen_cve
- class: deser
- cwe: CWE-502
- cve: ['CVE-2025-2855']
- severity: low
- quality_score: 14

## Scenario

What privileges or interaction does CVE-2025-2855 require?

## Analysis / Response

NVD scores CVE-2025-2855 at 7.2 (High) using CVSS 3.1, while the CNA (cna@vuldb.com) assigned 4.7 (Medium); this record uses the NVD primary score for its severity. The vector CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:H/I:H/A:H for CVE-2025-2855 means it is exploitable over the network, with low attack complexity, with high privileges, and with no user interaction; the scope stays within the vulnerable component, with high confidentiality, high integrity and high availability impact. Deserialization bugs in middleware affect every application that uses the component. Prioritization of CVE-2025-2855 should combine its high rating with how exposed Eladmin is in your environment.

**Remediation:** Avoid deserializing untrusted data. Use safe serialization formats (JSON) instead of binary formats. Implement integrity checks (digital signatures) on serialized data. Use class allowlists for deserialization. Monitor deserialization operations.
