# REDIRECT — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: redirect
- cve: ['CVE-2020-29565']

## Scenario

Give me a source-grounded overview of CVE-2020-29565.

## Analysis / Response

CVE-2020-29565: An issue was discovered in OpenStack Horizon before 15.3.2, 16.x before 16.2.1, 17.x and 18.x before 18.3.3, 18.4.x, and 18.5.x. There is a lack of validation of the "next" parameter, which would allow someone to supply a malicious URL in Horizon that can cause an automatic redirect to the provided malicious URL.

Source: https://nvd.nist.gov/vuln/detail/CVE-2020-29565
