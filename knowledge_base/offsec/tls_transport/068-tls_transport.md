# TLS_TRANSPORT — h1

- source: h1
- class: tls_transport
- cwe: CWE-297
- cve: ['CVE-2025-15079']
- severity: low
- program: curl
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2025-15079: libssh global knownhost override 
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
libssh has `SSH_OPTIONS_GLOBAL_KNOWNHOSTS` that specifies a global known_hosts file that will be used if the host is not found from the file specified in `SSH_OPTIONS_KNOWNHOSTS` file. libcurl `CURLOPT_SSH_KNOWNHOSTS` doesn't specify an invalid (or `/dev/null`) path to `SSH_OPTIONS_GLOBAL_KNOWNHOSTS` resulting in libcurl accepting any host identities that might be specified in the default file. This is significant when user tries to limit the known hosts to ones specified in their own file, as the global file will be checked if no match is found from the user specified file.

By default this file is `/etc/ssh/ssh_known_hosts`, and thus not modifiable by non-privileged user (at least on major platforms). Thus in most situations this issue cannot be exploited by actively modifying the file. This limits the impact of this flaw.

## Affected version
8.17.0

## Steps To Reproduce:

  1. Configure and compile curl with `--with-libssh`
  2. Add valid host entry for `host.example` to `/etc/ssh/ssh_known_hosts`
  3. `echo "" > knownhosts`
  4. `curl --knownhosts knownhosts [REDACTED_EMAIL]`

The host identity validation succeeds even though it should not.

## Remediation
- Make `CURLOPT_SSH_KNOWNHOSTS` set `SSH_OPTIONS_GLOBAL_KNOWNHOSTS` to `/dev/null` (or some non-existing path?).

## Supporting Material/References:
  * https://github.com/libssh/libssh-mirror/blob/ac6d2fad4a8bf[REDACTED_PHONE]e[REDACTED_PHONE]f/src/options.c#L304
  * https://github.com/libssh/libssh-mirror/blob/ac6d2fad4a8bf[REDACTED_PHONE]e[REDACTED_PHONE]f/src/knownhosts.c#L1176

## Impact

## Summary:
Host validation unexpectedly succeeding.

**Steps to Reproduce:**
1. Configure and compile curl with `--with-libssh`
  2. Add valid host entry for `host.example` to `/etc/ssh/ssh_known_hosts`
  3. `echo "" > knownhosts`
  4. `curl --knownhosts knownhosts [REDACTED_EMAIL]`

The host identity validation succeeds even though it should not.

## Analysis / Response

**Vulnerability Class:** tls_transport
**CWE:** CWE-297
**Weakness:** Improper Validation of Certificate with Host Mismatch
**Severity:** low
**Endpoint Pattern:** https://github.com/libssh/libssh-mirror/blob/ac6d2fad4a8bf07277127736367e90387646363f/src/options.c#L304

**Impact Assessment:**
## Summary:
Host validation unexpectedly succeeding.

**Remediation:**
- Make `CURLOPT_SSH_KNOWNHOSTS` set `SSH_OPTIONS_GLOBAL_KNOWNHOSTS` to `/dev/null` (or some non-existing path?).

## Supporting Material/References:
  * https://github.com/libssh/libssh-mirror/blob/ac6d2fad4a8bf[REDACTED_PHONE]e[REDACTED_PHONE]f/src/options.c#L304
  * https://github.com/libssh/libssh-mirror/blob/ac6d2fad4a8bf[REDACTED_PHONE]e[REDACTED_PHONE]f/src/knownhosts.c#L1176
