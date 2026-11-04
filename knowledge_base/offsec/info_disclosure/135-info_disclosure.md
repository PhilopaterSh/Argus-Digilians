# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2023-3345']
- severity: medium
- quality_score: 12

## Scenario

How do I harden LMS by Masteriyo against CVE-2023-3345?

## Analysis / Response

Fixing CVE-2023-3345 in LMS by Masteriyo:

1) Patch: The fix ships in LMS by Masteriyo 1.6.8; move every instance to that release or newer.

2) Hardening: Block POST /wp-login.php at the reverse proxy if the feature is not needed. Rotate any secrets LMS by Masteriyo may have exposed, such as API keys and database passwords.

3) References: https://wpscan.com/vulnerability/0d07423e-98d2-43a3-824d-562747a3d65a, https://github.com/RandomRobbieBF/learning-management-system, https://wordpress.org/plugins/learning-management-system

4) Confirm the fix by re-testing POST /wp-login.php and checking the installed LMS by Masteriyo version.

**Security Impact:** Information disclosure exposes sensitive technical details, internal infrastructure information, credentials, or personal data that attackers can use to plan and execute targeted attacks.
