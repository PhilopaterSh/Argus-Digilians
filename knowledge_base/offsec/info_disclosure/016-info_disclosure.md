# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2023-23493']
- severity: medium
- quality_score: 10

## Scenario

What versions fix CVE-2023-23493?

## Analysis / Response

Upgrade to a release that fixes CVE-2023-23493; the affected range ends before macos 12.6.3, macos 13.2, so moving to that version or later removes the flaw. Patch or advisory references for CVE-2023-23493: https://support.apple.com/en-us/HT213604; https://support.apple.com/en-us/HT213605. Additional hardening relevant to CVE-2023-23493:
- Write negative tests for unauthenticated access.
- Enable multi-factor authentication for administrators.
- Log authentication failures and anomalies.
After patching, verify the installed version of Apple Macos and review logs for signs that CVE-2023-23493 was abused before the fix.
