# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- severity: high
- quality_score: 11

## Scenario

How do defenders spot exploitation of authentication bypass?

## Analysis / Response

Detection approaches for authentication bypass: Review routing and middleware to confirm every sensitive route enforces authentication, including alternate encodings and methods. Monitor logs for successful access to admin endpoints without a prior login, requests with path tricks (`;`, `..;/`, double slashes, case changes) and spoofed headers. Optional Nuclei templates test known product bypasses. Patterns include an auth filter matching `/admin/*` while the router also accepts `/admin;/` or `/ADMIN`, middleware that is skipped for certain HTTP methods, code such as `if request.headers.get('X-Forwarded-For') == '127.0.0.1': allow()`, cookies like `isAdmin=true`, and setup or recovery endpoints left reachable after installation. MFA reduces the value of stolen credentials but not of logic bypasses. Edge appliances are frequent targets for authentication bypass exploitation.

**Remediation:** Implement multi-factor authentication. Use established authentication frameworks (OAuth 2.0, OIDC). Enforce strong password policies. Implement account lockout after failed attempts. Secure session management with proper token handling.
