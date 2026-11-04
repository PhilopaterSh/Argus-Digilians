# PATHTRAVER — h1

- source: h1
- class: pathtraver
- cwe: CWE-22
- severity: high
- program: lichess
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Path Traversal Vulnerability in Lila Project
**Affected Asset:** https://github.com/lichess-org/lila

**Vulnerability Description:**
## Summary:
A path traversal vulnerability was discovered in the Lila project that allows an attacker to access arbitrary files on the server by manipulating user-supplied input to traverse outside the intended directory structure. This flaw could potentially expose sensitive files such as application source code, configuration files, or other data not meant for public access.

## Steps To Reproduce:
[add details for how we can reproduce the issue]
code url
lila-master/conf/routes,line 939
{F4420388}
poc
https://lichess.org/assets/../build.sbt
{F4420380}
https://lichess.org/assets/../.git/config
{F4420382}

## Supporting Material/References:
[list any additional material (e.g. screenshots, logs, etc.)]

  * [attachment / reference]

## Impact

The path traversal vulnerability in the Lila project could lead to:
Arbitrary file read: An attacker could access sensitive files such as:
.git/config, revealing repository structure and remote URLs
application.conf or similar, leaking secrets, DB credentials, or API keys
Server-side source files, enabling reverse engineering or bug discovery
Information disclosure: Internal logic, credentials, deployment details, or admin-only configurations may be exposed.
Privilege escalation (indirectly): By reading files related to user tokens or access control, an attacker might craft further exploits.
Recon for further attacks: Knowledge of internal file structure aids in targeting further vulnerabilities like RCE or IDOR.

**Steps to Reproduce:**
[add details for how we can reproduce the issue]
code url
lila-master/conf/routes,line 939
{F4420388}

**Proof of Concept:**
https://lichess.org/assets/../build.sbt
{F4420380}
https://lichess.org/assets/../.git/config
{F4420382}

## Supporting Material/References:
[list any additional material (e.g. screenshots, logs, etc.)]

  * [attachment / reference]

## Analysis / Response

**Vulnerability Class:** pathtraver
**CWE:** CWE-22
**Weakness:** Path Traversal: '.../...//'
**Severity:** high
**Endpoint Pattern:** https://lichess.org/assets/../build.sbt

**Impact Assessment:**
The path traversal vulnerability in the Lila project could lead to:
Arbitrary file read: An attacker could access sensitive files such as:
.git/config, revealing repository structure and remote URLs
application.conf or similar, leaking secrets, DB credentials, or API keys
Server-side source files, enabling reverse engineering or bug discovery
Information disclosure: Internal logic, credentials, deployment details, or admin-only configurations may be exposed.
Privilege escalation (indirectly): By reading files related to user tokens or access control, an attacker might craft further exploits.
Recon for further attacks: Knowledge of internal file structure aids in targeting further vulnerabilities like RCE or IDOR.

**Remediation:**
Validate file paths against an allowlist of permitted directories. Use canonical path resolution. Never use user input directly in filesystem operations.
