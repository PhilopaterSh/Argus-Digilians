# CMDI — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: cmdi
- cve: ['CVE-2020-7799']

## Scenario

Give me a source-grounded overview of CVE-2020-7799.

## Analysis / Response

CVE-2020-7799: An issue was discovered in FusionAuth before 1.11.0. An authenticated user, allowed to edit e-mail templates (Home -> Settings -> Email Templates) or themes (Home -> Settings -> Themes), can execute commands on the underlying operating system by abusing freemarker.template.utility.Execute in the Apache FreeMarker engine that processes custom templates.

Source: https://nvd.nist.gov/vuln/detail/CVE-2020-7799
