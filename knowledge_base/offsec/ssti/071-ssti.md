# SSTI — qwen_cve

- source: qwen_cve
- class: ssti
- cwe: CWE-1336
- cve: ['CVE-2024-42355']
- severity: high
- quality_score: 11

## Scenario

Give me an overview of CVE-2024-42355.

## Analysis / Response

CVE-2024-42355 is a Server-Side Template Injection (SSTI) vulnerability in Shopware. The NVD entry for CVE-2024-42355 reads: Shopware, an open ecommerce platform, has a new Twig Tag `sw_silent_feature_call` which silences deprecation messages while triggered in this tag. Prior to versions 6.6.5.1 and 6.5.8.13, it accepts as parameter a string the feature flag name to silence, but this parameter is not escaped properly and allows execution of code. Update to Shopware 6.6.5.1 or 6.5.8.13 to receive a patch. For older versions of 6.2, 6.3, and 6.4, corresponding security measures are also available via a plugin. An SSTI probe typically checks whether arithmetic like 7*7 inside template delimiters is evaluated. The weakness recorded for CVE-2024-42355 is CWE-1336, CWE-94.
