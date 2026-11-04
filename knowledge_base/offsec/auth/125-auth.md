# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2025-41393']
- severity: critical
- quality_score: 12

## Scenario

Break down the CVSS impact of CVE-2025-41393.

## Analysis / Response

Attackers can execute malicious JavaScript in user browsers through the profile parameter, potentially leading to session hijacking and credential theft.

Exploiting CVE-2025-41393 requires access over the network, without any account.

The CVSS v3 base score for CVE-2025-41393 is 5.1, which rates as medium. Scores for CVE-2025-41393 differ by source: the Nuclei template lists 6.1, while the NVD primary score is 5.1; the NVD primary score is used here.

Patch Ricoh Web Image Monitor in the normal cycle, prioritising instances reachable from untrusted networks.
