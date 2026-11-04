# CSRF — qwen_cve

- source: qwen_cve
- class: csrf
- cwe: CWE-352
- severity: medium
- quality_score: 10

## Scenario

Common anti-patterns in missing or broken authorization remediation?

## Analysis / Response

Incomplete missing or broken authorization remediation commonly looks like this. Fixes often add checks to the UI or one endpoint while sibling endpoints or API versions remain open. Nonce checks in WordPress verify intent, not permission, and are sometimes mistaken for authorization. API versions and mobile endpoints often lag behind web authorization fixes. WordPress nonces protect against CSRF but are not capability checks.

**Security Impact:** Cross-site request forgery allows an attacker to trick authenticated users into performing unintended actions such as changing passwords, transferring funds, or modifying account settings.
