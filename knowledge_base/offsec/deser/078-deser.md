# DESER — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: deser
- cve: ['CVE-2023-25135']

## Scenario

Give me a source-grounded overview of CVE-2023-25135.

## Analysis / Response

CVE-2023-25135: vBulletin before 5.6.9 PL1 allows an unauthenticated remote attacker to execute arbitrary code via a crafted HTTP request that triggers deserialization. This occurs because verify_serialized checks that a value is serialized by calling unserialize and then checking for errors. The fixed versions are 5.6.7 PL1, 5.6.8 PL1, and 5.6.9 PL1.

Source: https://nvd.nist.gov/vuln/detail/CVE-2023-25135
