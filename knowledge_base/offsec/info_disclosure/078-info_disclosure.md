# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2017-11165']
- severity: critical
- quality_score: 15

## Scenario

Quick rundown of CVE-2017-11165, please.

## Analysis / Response

CVE-2017-11165 is an information disclosure vulnerability in DataTaker DT80 dEX.

dataTaker DT80 dEX 1.50.012 allows remote attackers to obtain sensitive credential and configuration information via a direct request for the /services/getFile.cmd?userfile=config.xml URI. It maps to CWE-200.

Root cause: DataTaker DT80 dEX returns sensitive data such as configuration, credentials, versions or internal paths to unauthenticated callers.

CVE-2017-11165 has a CVSS v3 base score of 9.8 (critical).

Impact: Successful exploitation of this vulnerability could lead to unauthorized access to sensitive data, potentially compromising the confidentiality of the system.
