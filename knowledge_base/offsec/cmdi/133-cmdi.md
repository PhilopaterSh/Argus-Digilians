# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2021-46418']
- severity: high
- quality_score: 15

## Scenario

Give me the key facts about CVE-2021-46418.

## Analysis / Response

CVE-2021-46418 is a web application flaw vulnerability in Telesquare TLR.

An unauthorized file creation vulnerability in Telesquare TLR-2855KS6 via PUT method can allow creation of CGI scripts.

Root cause: a logic or configuration flaw in Telesquare TLR is reachable over HTTP.

For CVE-2021-46418, CVSS v3 gives a base score of 7.5 (high).

Impact: Unauthenticated attackers can create arbitrary files including CGI scripts via HTTP PUT requests, potentially achieving remote code execution.
