# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2021-31195']
- severity: high
- quality_score: 14

## Scenario

What is the impact of CVE-2021-31195?

## Analysis / Response

Successful exploitation of this vulnerability could allow an attacker to execute arbitrary script code in the context of the user's browser, potentially leading to session hijacking, data theft, or other malicious activities.

An attacker can reach Microsoft Exchange Server for this over the network, without any account, only if a user is tricked into an action, per the CVSS vector.

CIA breakdown of CVE-2021-31195: confidentiality impact is high, integrity impact is high and availability impact is high.

CVE-2021-31195 has a CVSS v3 base score of 8.8 (high). For reference, the CNA gives CVE-2021-31195 6.5 whereas NVD's primary score is 8.8, and NVD primary is the scoring policy for this dataset.

Schedule the Microsoft Exchange Server fix in the current patch cycle, sooner if it is exposed to the internet.
