# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2022-34487']
- severity: medium
- quality_score: 12

## Scenario

What's the remediation for CVE-2022-34487?

## Analysis / Response

Fixing CVE-2022-34487 in ShortCode Addons:

1) Patch: No fixed version of ShortCode Addons is recorded here, so confirm the patched release from the vendor references before upgrading.

2) Compensating controls for CVE-2022-34487: Restrict network access to ShortCode Addons until patched. Review the ShortCode Addons configuration against the vendor hardening guide.

3) References: https://wpscan.com/vulnerability/c8dd91d5-fdc4-4852-9823-6d0047b214fe/, https://patchstack.com/database/vulnerability/shortcode-addons/wordpress-shortcode-addons-plugin-3-0-3-unauthenticated-arbitrary-option-update-vulnerability, https://wordpress.org/plugins/shortcode-addons/#developers

4) Confirm the fix by re-testing POST /wp-json/ShortCodeAddonsUltimate/v2/addons_settings and checking the installed ShortCode Addons version.

**Security Impact:** Information disclosure exposes sensitive technical details, internal infrastructure information, credentials, or personal data that attackers can use to plan and execute targeted attacks.
