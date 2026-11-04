# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- severity: high
- quality_score: 11

## Scenario

How do I tell insecure direct object reference (IDOR) apart when triaging?

## Analysis / Response

Here is how insecure direct object reference (IDOR) compares with similar issues. IDOR is object-level authorization; missing function-level authorization concerns whole actions. Path traversal manipulates file paths rather than record identifiers, though both involve user-controlled references. API security lists call it BOLA (API1:2023). Every record lookup should be scoped to the requesting user or tenant. GraphQL resolvers are a frequent IDOR source. Two-account testing is the standard IDOR test technique.

**Security Impact:** Path traversal allows reading arbitrary files from the server, exposing sensitive configuration files, source code, credentials, and private keys that can facilitate further attacks.

**Remediation:** Canonicalize and validate all file paths. Use a chroot jail or sandboxed directory. Implement path allowlists. Strip or reject sequences like ../ and null bytes. Use framework-provided secure file access APIs.
