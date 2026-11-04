# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2019-5128']
- severity: critical
- quality_score: 11

## Scenario

What version fixes CVE-2019-5128?

## Analysis / Response

Remediation for CVE-2019-5128 (YouPHPTube Encoder):

1) Patch: The source data does not name a fixed release of YouPHPTube Encoder; check the vendor advisory below for the patched version and apply it.

2) Defence in depth for YouPHPTube Encoder: Remove shell invocation in YouPHPTube Encoder where possible and pass arguments as arrays, never concatenated strings. Restrict who can reach GET /objects/getImageMP4.php?base64Url=[payload]&format=jpg (VPN, allow-lists) until the fix is applied.

3) References: https://xz.aliyun.com/news/6312, https://talosintelligence.com/vulnerability_reports/TALOS-2019-0917

4) Verify by re-running the CVE-2019-5128 check on GET /objects/getImageMP4.php?base64Url=[payload]&format=jpg; the indicators should be gone.
