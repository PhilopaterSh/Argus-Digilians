# UNCATEGORIZED — NVD CVE 2.0 annual feed

- source: NVD CVE 2.0 annual feed
- class: uncategorized
- cve: ['CVE-2025-1974']

## Scenario

Give me a source-grounded overview of CVE-2025-1974.

## Analysis / Response

CVE-2025-1974: A security issue was discovered in Kubernetes where under certain conditions, an unauthenticated attacker with access to the pod network can achieve arbitrary code execution in the context of the ingress-nginx controller. This can lead to disclosure of Secrets accessible to the controller. (Note that in the default installation, the controller can access all Secrets cluster-wide.)

Source: https://nvd.nist.gov/vuln/detail/CVE-2025-1974
