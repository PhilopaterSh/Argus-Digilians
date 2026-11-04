# TLS_TRANSPORT — h1

- source: h1
- class: tls_transport
- cwe: CWE-295
- cve: ['CVE-2026-111484', 'CVE-2026-111953', 'CVE-2026-7009']
- severity: low
- program: curl
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2026-111953: GnuTLS SecTrust OCSP staple bypass
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
When curl is built with GnuTLS and Apple SecTrust, as MacPorts does for `curl +gnutls +sectrust`, a failed GnuTLS verification is handed to SecTrust, and if SecTrust accepts the chain the GnuTLS result is dropped (lib/vtls/gtls.c:1511-1521 in 8.23.0). SecTrust is called without the stapled OCSP response, so when GnuTLS failed because of the staple (revoked, bad signature, out of date), nothing looks at the staple again: 8.23.0 only checks that one was sent (gtls.c:1436-1451), and master reads the status code but assumes GnuTLS has already verified the signature and the time (gtls.c:1479-1483). As a result --cert-status accepts a correctly signed "revoked" staple on 8.23.0, and a staple with a forged signature or an expired one on 8.23.0 and on current master. The clearest way to see it, on 8.23.0 with a revoked staple: `curl --cacert root.pem --cert-status URL` fails with (60), the same command with `--ca-native` added returns HTTP 200, and so do default options, because SecTrust builds use the native store unless a CA file is given (lib/vtls/vtls_config.c:287-288). This is a separate code path from my report #4118610 (OpenSSL with SecTrust, CVE-[REDACTED_PHONE]): its fix cd89b5178b passes `NULL, 0, FALSE` here on purpose ("We check OCSP separately"), and the GnuTLS fix 287df0b324 only added the status code check.

## Affected version
8.23.0 accepts revoked, forged and stale staples; master 629646d9b7 accepts forged and stale ones. 8.20.0 accepts forged and stale staples too (tested), and 8.18.0 to 8.20.x have the same code here. The fallback came with eefd03c[REDACTED_PHONE]), where it only ran for GNUTLS_CERT_SIGNER_NOT_FOUND, that is for roots GnuTLS does not have; 6aa8fa3fdf (8.18.0, "Do the same for GnuTLS") made it run for every GnuTLS failure, including failures caused by the staple. 8.22.0 rejected every intermediate-signed staple in my tests, good ones included, because of the be6c4ee7fa signature check that 8.21.0 also has (see curl PR 23311). That commit also reasoned that a bad staple cannot pass with peer verification on, because gnutls_certificate_verify_peers2() catches it; this fallback is the case that reasoning did not cover.

MacPorts builds `curl +gnutls +sectrust` with `--with-gnutls --with-ca-bundle=... --with-apple-sectrust`. The variant has existed since at least its 8.19.0 port (and +http3 requires +gnutls); the current 8.22.0 port is in the fail-closed window, 8.19.0 and 8.20.0 were affected, and 8.23.0 will be once the port is updated.

Tested on macOS 27.0.1 arm64, Homebrew GnuTLS 3.8.13, curl built from the curl-8_23_0, curl-8_22_0 and curl-8_20_0 tags and from master with `-DCURL_USE_GNUTLS=ON -DUSE_APPLE_SECTRUST=ON`, without a CA bundle, and for 8.23.0 and master als

## Analysis / Response

**Vulnerability Class:** tls_transport
**CWE:** CWE-295
**Weakness:** Improper Certificate Validation
**Severity:** low
**Endpoint Pattern:** https://localhost:23003/

**Impact Assessment:**
--cert-status is documented to make the transfer fail when the stapled response is invalid or does not confirm the certificate. On GnuTLS builds with Apple SecTrust the staple stops being checked exactly when GnuTLS finds it bad, and this happens with default options. An attacker who holds the key of a revoked certificate and can intercept the connection passes --cert-status on 8.23.0 by stapling the CA's own current "revoked" response, and on 8.18.0 to 8.20.x and current master with an old or self-made "good" one, which is the attack OCSP stapling enforcement exists to stop. The conditions match CVE-2026-7009 and CVE-[REDACTED_PHONE] (both Medium) with GnuTLS in place of OpenSSL, in a configuration MacPorts ships as `curl +gnutls +sectrust`. libcurl applications that set CURLOPT_SSL_VERIFYSTATUS on such builds are affected the same way.

**Remediation:**
Hand the stapled response to SecTrust on this path and require a positive answer when verifystatus is set, as cd89b5178b does for OpenSSL. With that change on master (fix/gtls-sectrust-ocsp-fix.diff, 03-fix-check.txt) only the good staples pass, with default options and with --cacert plus --ca-native, on TLS 1.2 and 1.3, and nothing changes without --cert-status. Another option is to not let the fallback override a failure where GnuTLS set GNUTLS_CERT_REVOKED, GNUTLS_CERT_INVALID_OCSP_STATUS or GNUTLS_CERT_REVOCATION_DATA_SUPERSEDED; GnuTLS sets them even when it does not know the root (verify status 98, 1048642 and 4162 in 03-fix-check.txt).

AI disclosure: I used an AI assistant (Claude) for code review, test setup and drafting. I reproduced every result myself on curl built from the curl-8_23_0, curl-8_22_0 and curl-8_20_0 tags and from master; the attached logs are the raw output.
