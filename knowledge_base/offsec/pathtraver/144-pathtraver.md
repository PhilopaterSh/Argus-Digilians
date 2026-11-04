# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- cve: ['CVE-2021-41151']
- severity: high
- quality_score: 13

## Scenario

How should developers address CVE-2021-41151?

## Analysis / Response

Upgrade to a release that fixes CVE-2021-41151; the affected range ends before backstage 0.15.9, so moving to that version or later removes the flaw. Patch or advisory references for CVE-2021-41151: https://github.com/backstage/backstage/commit/6968962c920508eae19a4c1c200fa2c8980a4006. Additional hardening relevant to CVE-2021-41151:
- Store sensitive configuration outside the web root and outside any directory the app can enumerate.
- When extracting archives, validate each entry path to prevent zip-slip writes.
- Use opaque identifiers that map to files server-side instead of accepting file names from the client.
Once CVE-2021-41151 is fixed, confirm the deployed build and check historical access logs for suspicious requests.

**Security Impact:** Path traversal allows reading arbitrary files from the server, exposing sensitive configuration files, source code, credentials, and private keys that can facilitate further attacks.
