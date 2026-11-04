# CMDI — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: cmdi
- cve: ['CVE-2025-1097']

## Scenario

Give me a source-grounded overview of CVE-2025-1097.

## Analysis / Response

CVE-2025-1097: A security issue was discovered in  ingress-nginx https://github.com/kubernetes/ingress-nginx  where the `auth-tls-match-cn` Ingress annotation can be used to inject configuration into nginx. This can lead to arbitrary code execution in the context of the ingress-nginx controller, and disclosure of Secrets accessible to the controller. (Note that in the default installation, the controller can access all Secrets cluster-wide.)

Source: https://nvd.nist.gov/vuln/detail/CVE-2025-1097
