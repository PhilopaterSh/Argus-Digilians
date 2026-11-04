# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- severity: high
- quality_score: 12

## Scenario

Explain detection of authentication bypass for a blue team.

## Analysis / Response

Detecting authentication bypass combines code review and runtime monitoring. Review routing and middleware to confirm every sensitive route enforces authentication, including alternate encodings and methods. Monitor logs for successful access to admin endpoints without a prior login, requests with path tricks (`;`, `..;/`, double slashes, case changes) and spoofed headers. Optional Nuclei templates test known product bypasses. Authorized testers enumerate endpoints, request them without a session, with altered paths, methods and headers, and compare responses to authenticated ones, using non-destructive read operations as proof. Client-supplied headers like X-Forwarded-For must not grant trust. After patching a bypass, rotate secrets and review for compromise.

**Security Impact:** Authentication bypass allows unauthorized users to access protected resources, impersonate legitimate users, escalate privileges, and compromise the security of the entire application.
