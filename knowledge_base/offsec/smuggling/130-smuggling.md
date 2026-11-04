# SMUGGLING — qwen_cve

- source: qwen_cve
- class: smuggling
- cwe: CWE-444
- cve: ['CVE-2021-29991']
- severity: high
- quality_score: 11

## Scenario

Our scanner reports CVE-2021-29991. How do we remediate it?

## Analysis / Response

Upgrade to a release that fixes CVE-2021-29991; the affected range ends before firefox 91.0.1, thunderbird 91.0.1, so moving to that version or later removes the flaw. Patch or advisory references for CVE-2021-29991: https://www.mozilla.org/security/advisories/mfsa2021-37/. Beyond the fix for CVE-2021-29991, these HTTP Request Smuggling hardening measures help:
- Reject malformed chunked encoding.
- Test with smuggling detection tools.
- Upgrade proxies and servers to versions with strict parsing.
Once CVE-2021-29991 is fixed, confirm the deployed build and check historical access logs for suspicious requests.

**Security Impact:** HTTP request smuggling enables cache poisoning, credential hijacking, bypassing security controls, and request routing manipulation affecting other users.
