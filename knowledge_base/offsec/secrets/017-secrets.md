# SECRETS — h1

- source: h1
- class: secrets
- cwe: CWE-312
- cve: ['CVE-2023-48305']
- severity: medium
- program: nextcloud
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** user_ldap app logs user passwords in the log file on level debug
**Affected Asset:** nextcloud/server

**Vulnerability Description:**
## Summary:
Nextcloud using ldap user authentication and loglevel debug write user passwords to log file.
Vulnerable versions: 26.0.4, 27.0.1.

## Steps To Reproduce:
  1. Use a nextcloud with ldap user authentication.
  2. Set nextcloud config loglevel to 0 (debug).
  3. Login to nextcloud using a ldap user.
  4. Search for lines with 'ldap_bind' in nextcloud log file.

## Supporting Material/References:
Sample log file:
```
{"reqId":"QRqbkhMpRAY1ugvQMrPk","level":0,"time":"[REDACTED_PHONE]T11:17:11-03:00","remoteAddr":"<IPADDRESS>","user":"--","app":"user_ldap","method":"POST","url":"/login","message":"Calling LDAP function ldap_bind with parameters [{},\"uid=<USERNAME>\",\"<PASSWORD>\"]","userAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36","version":"27.0.1.2","data":{"app":"user_ldap"}}
```

Affected file:
`apps/user_ldap/lib/LDAP.php`

Vulnerable code:
```
	private function preFunctionCall(string $functionName, array $args): void {
		$this->curArgs = $args;
		$this->logger->debug('Calling LDAP function {func} with parameters {args}', [
			'app' => 'user_ldap',
			'func' => $functionName,
			'args' => json_encode($args),
		]);
```

## Impact

Local administrator can retriave user passwords.

**Steps to Reproduce:**
1. Use a nextcloud with ldap user authentication.
  2. Set nextcloud config loglevel to 0 (debug).
  3. Login to nextcloud using a ldap user.
  4. Search for lines with 'ldap_bind' in nextcloud log file.

## Supporting Material/References:
Sample log file:
```
{"reqId":"QRqbkhMpRAY1ugvQMrPk","level":0,"time":"[REDACTED_PHONE]T11:17:11-03:00","remoteAddr":"<IPADDRESS>","user":"--","app":"user_ldap","method":"POST","url":"/login","message":"Calling LDAP function ldap_bind with parameters [{},\"uid=<USERNAME>\",\"<PASSWORD>\"]","userAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36","version":"27.0.1.2","data":{"app":"user_ldap"}}
```

Affected file:
`apps/user_ldap/lib/LDAP.php`

Vulnerable code:
```
	private function preFunctionCall(string $functionName, array $args): void {
		$this->curArgs = $args;
		$this->logger->debug('Calling LDAP function {func} with parameters {args}', [
			'app' => 'user_ldap',
			'func' => $functionName,
			'args' => json_encode($args),
		]);
```

**Proof of Concept:**
```
{"reqId":"QRqbkhMpRAY1ugvQMrPk","level":0,"time":"[REDACTED_PHONE]T11:17:11-03:00","remoteAddr":"<IPADDRESS>","user":"--","app":"user_ldap","method":"POST","url":"/login","message":"Calling LDAP function ldap_bind with parameters [{},\"uid=<USERNAME>\",\"<PASSWORD>\"]","userAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.

## Analysis / Response

**Vulnerability Class:** secrets
**CWE:** CWE-312
**Weakness:** Cleartext Storage of Sensitive Information
**Severity:** medium
**Endpoint Pattern:** https://github.com/nextcloud/security-advisories/security/advisories/GHSA-35p6-4992-w5fr

**Impact Assessment:**
Local administrator can retriave user passwords.

Security advisory at https://github.com/nextcloud/security-advisories/security/advisories/GHSA-35p6-4992-w5fr

**Remediation:**
Remove hardcoded secrets from source code. Use environment variables or secret management services. Rotate exposed credentials immediately.
