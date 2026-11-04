# SMUGGLING — qwen_cve

- source: qwen_cve
- class: smuggling
- cwe: CWE-444
- cve: ['CVE-2021-31922']
- severity: high
- quality_score: 11

## Scenario

What versions fix CVE-2021-31922?

## Analysis / Response

Upgrade to a release that fixes CVE-2021-31922; the affected range ends before 21.1, so moving to that version or later removes the flaw. Patch or advisory references for CVE-2021-31922: https://kb.pulsesecure.net/articles/Pulse_Security_Advisories/SA44790. Beyond the fix for CVE-2021-31922, these HTTP Request Smuggling hardening measures help:
- Apply vendor patches.
- Review CDN parsing settings.
- Normalize ambiguous requests at the edge.
Once CVE-2021-31922 is fixed, confirm the deployed build and check historical access logs for suspicious requests.

**Security Impact:** HTTP request smuggling enables cache poisoning, credential hijacking, bypassing security controls, and request routing manipulation affecting other users.
