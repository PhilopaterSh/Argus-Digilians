# SSRF — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: ssrf
- cve: ['CVE-2023-39109']

## Scenario

What does the CVE Program record say about CVE-2023-39109?

## Analysis / Response

CVE-2023-39109: rconfig v3.9.4 was discovered to contain a Server-Side Request Forgery (SSRF) via the path_a parameter in the doDiff Function of /classes/compareClass.php. This vulnerability allows authenticated attackers to make arbitrary requests via injection of crafted URLs.

Source: https://nvd.nist.gov/vuln/detail/CVE-2023-39109
