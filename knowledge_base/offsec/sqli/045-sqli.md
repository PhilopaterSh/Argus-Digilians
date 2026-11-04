# SQLI — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: sqli
- cve: ['CVE-2026-53629']

## Scenario

Give me a source-grounded overview of CVE-2026-53629.

## Analysis / Response

CVE-2026-53629: GLPI is a free asset and IT management software package. From 9.4.0 until 10.0.26 and 11.0.8, an attacker with the READ right on logs can craft a URL for the history tab that injects attacker-controlled values into a database query. This permits SQL injection through the history tab endpoint. This issue is fixed in versions 11.0.8 and 10.0.26.

Source: https://nvd.nist.gov/vuln/detail/CVE-2026-53629
