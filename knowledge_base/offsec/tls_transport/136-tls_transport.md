# TLS_TRANSPORT — h1

- source: h1
- class: tls_transport
- cwe: CWE-295
- cve: ['CVE-2024-8096']
- severity: medium
- program: curl
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2024-8096: OCSP stapling bypass with GnuTLS
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
When the TLS backend is GnuTLS, there is an issue with the OCSP stapling validation process. As a result, even if the certificate is revoked, the connection can be established without resulting in an error.

When the OCSP stapling status response is "revoked," gnutls_certificate_verify_peers2() returns an error. However, gnutls_certificate_verify_peers2() only returns an error when the OCSP status is "revoked." For other statuses, gnutls_certificate_verify_peers2() returns a successful result.

In curl, the verification of the OCSP stapling status response is performed not only with the above function but also with gnutls_ocsp_status_request_is_checked(). However, this function returns a non-zero value if the OCSP stapling status response exists. As a result, if any response exists, it is treated as a successful case, and the verification process concludes.

```
  if(config->verifystatus) {
    if(gnutls_ocsp_status_request_is_checked(session, 0) == 0) {
      gnutls_datum_t status_request;
      gnutls_ocsp_resp_t ocsp_resp;

      gnutls_ocsp_cert_status_t status;
      gnutls_x509_crl_reason_t reason;

      rc = gnutls_ocsp_status_request_get(session, &status_request);

      infof(data, " server certificate status verification FAILED");

      if(rc == GNUTLS_E_REQUESTED_DATA_NOT_AVAILABLE) {
        failf(data, "No OCSP response received");
        return CURLE_SSL_INVALIDCERTSTATUS;
      }

      if(rc < 0) {
        failf(data, "Invalid OCSP response received");
        return CURLE_SSL_INVALIDCERTSTATUS;
      }

      gnutls_ocsp_resp_init(&ocsp_resp);

      rc = gnutls_ocsp_resp_import(ocsp_resp, &status_request);
      if(rc < 0) {
        failf(data, "Invalid OCSP response received");
        return CURLE_SSL_INVALIDCERTSTATUS;
      }

      (void)gnutls_ocsp_resp_get_single(ocsp_resp, 0, NULL, NULL, NULL, NULL,
                                        &status, NULL, NULL, NULL, &reason);

      switch(status) {
      case GNUTLS_OCSP_CERT_GOOD:
        break;

      case GNUTLS_OCSP_CERT_REVOKED: {
        const char *crl_reason;

        switch(reason) {
          default:
          case GNUTLS_X509_CRLREASON_UNSPECIFIED:
            crl_reason = "unspecified reason";
            break;

          case GNUTLS_X509_CRLREASON_KEYCOMPROMISE:
            crl_reason = "private key compromised";
            break;

          case GNUTLS_X509_CRLREASON_CACOMPROMISE:
            crl_reason = "CA compromised";
            break;

          case GNUTLS_X509_CRLREASON_AFFILIATIONCHANGED:
            crl_reason = "affiliation has changed";
            break;

          case GNUTLS_X509_CRLREASON_SUPERSEDED:
            crl_reason = "certificate superseded";
            break;

          case GNUTL

## Analysis / Response

**Vulnerability Class:** tls_transport
**CWE:** CWE-295
**Weakness:** Improper Certificate Validation
**Severity:** medium
**Endpoint Pattern:** https://ocsp4test.sytes.net:4433

**Impact Assessment:**
Bypassing OCSP verification.

**Remediation:**
Enforce TLS 1.2+ for all connections. Enable HSTS. Disable weak cipher suites. Use certificate pinning for mobile applications.
