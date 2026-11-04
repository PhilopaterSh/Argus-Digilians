# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-862
- cve: ['CVE-2010-1953']
- severity: medium
- quality_score: 13

## Scenario

Give me mitigation steps for CVE-2010-1953.

## Analysis / Response

Remediation for CVE-2010-1953 (Joomla! Component iNetLanka Multiple Map):

1) Patch: No fixed version of Joomla! Component iNetLanka Multiple Map is recorded here, so confirm the patched release from the vendor references before upgrading.

2) Defence in depth for Joomla! Component iNetLanka Multiple Map: Map user choices in Joomla! Component iNetLanka Multiple Map to an allow-list of file identifiers instead of raw paths. Run Joomla! Component iNetLanka Multiple Map with least-privilege filesystem permissions so sensitive files such as /etc/passwd or config files are unreadable.

3) References: http://www.vupen.com/english/advisories/2010/0927, http://secunia.com/advisories/39530, http://www.securityfocus.com/bid/39551, https://www.exploit-db.com/exploits/12288

4) Verify by re-running the CVE-2010-1953 check on GET /index.php?option=com_multimap&controller=../../../../../../../../../../etc/passwd%00; the indicators should be gone.
