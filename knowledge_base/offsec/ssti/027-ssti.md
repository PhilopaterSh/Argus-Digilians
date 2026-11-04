# SSTI — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: ssti
- cve: ['CVE-2026-119144']

## Scenario

Summarize the official record for CVE-2026-119144.

## Analysis / Response

CVE-2026-119144: Frappe Framework before 15.111.0 and 16.x before 16.21.0 contains a server-side template injection vulnerability because user-controlled message fields are rendered as templates without neutralization. An authenticated attacker holding a common operational role can inject template expressions that the server evaluates in an unrestricted context.

Source: https://nvd.nist.gov/vuln/detail/CVE-2026-119144
