# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2015-5910']
- severity: medium
- quality_score: 11

## Scenario

What's the story behind CVE-2015-5910?

## Analysis / Response

CVE-2015-5910 is an Information Disclosure vulnerability in Apple Xcode. NVD describes CVE-2015-5910 as follows: IDE Xcode Server in Apple Xcode before 7.0 does not ensure that server traffic is encrypted, which allows remote attackers to obtain sensitive information by sniffing the network. CWE-200 covers exposure of sensitive information. The weakness recorded for CVE-2015-5910 is CWE-200.

**Remediation:** Remove detailed error messages in production. Disable debug modes and directory listings. Sanitize API responses to exclude internal details. Implement proper access controls on sensitive files. Review HTTP response headers.
