# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-347
- cve: ['CVE-2024-45409']
- severity: critical
- quality_score: 13

## Scenario

I saw CVE-2024-45409 in a scan report. What is it?

## Analysis / Response

In short, CVE-2024-45409 is a cryptographic weakness issue in GitLab.

The Ruby SAML library is for implementing the client side of a SAML authorization. Ruby-SAML in <= 12.2 and 1.13.0 <= 1.16.0 does not properly verify the signature of the SAML Response. An unauthenticated attacker with access to any signed saml document (by the IdP) can thus forge a SAML Response/Assertion with arbitrary contents. This would allow the attacker to log in as arbitrary user within the vulnerable system. This vulnerability is fixed in 1.17.0 and 1.12.3. It maps to CWE-347.

Root cause: GitLab accepts tokens signed with a known or default secret.

For CVE-2024-45409, CVSS v3 gives a base score of 10.0 (critical). Scores for CVE-2024-45409 differ by source: the Nuclei template lists 9.8, while the NVD primary score is 10.0; the NVD primary score is used here.

Impact: An unauthenticated attacker with access to any signed saml document (by the IdP) can thus forge a SAML Response/Assertion with arbitrary contents. This would allow the attacker to log in as arbitrary user within the vulnerable system.
