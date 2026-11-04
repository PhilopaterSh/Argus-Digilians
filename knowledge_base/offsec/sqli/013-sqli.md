# SQLI — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: sqli
- cve: ['CVE-2022-3142']

## Scenario

Summarize the official record for CVE-2022-3142.

## Analysis / Response

CVE-2022-3142: The NEX-Forms WordPress plugin before 7.9.7 does not properly sanitise and escape user input before using it in SQL statements, leading to SQL injections. The attack can be executed by anyone who is permitted to view the forms statistics chart, by default administrators, however can be configured otherwise via the plugin settings.

Source: https://nvd.nist.gov/vuln/detail/CVE-2022-3142
