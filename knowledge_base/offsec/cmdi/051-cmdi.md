# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2020-6975']
- severity: low
- quality_score: 13

## Scenario

How urgent is patching CVE-2020-6975?

## Analysis / Response

NVD scores CVE-2020-6975 at 4.9 (Medium) using CVSS 3.1. The vector CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:N/I:H/A:N for CVE-2020-6975 means it is exploitable over the network, with low attack complexity, with high privileges, and with no user interaction; the scope stays within the vulnerable component, with no confidentiality, high integrity and no availability impact. Uploading a server-side script usually yields remote code execution. Teams running Digi Connectport Lts 32 Mei Bios should treat CVE-2020-6975 as medium priority and confirm exposure before scheduling the fix.
