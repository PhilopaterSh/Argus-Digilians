# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2016-1000127']
- severity: medium
- quality_score: 13

## Scenario

How bad is CVE-2016-1000127 if exploited?

## Analysis / Response

This vulnerability allows an attacker to execute arbitrary JavaScript code in the context of the victim's browser, potentially leading to session hijacking, defacement, or theft of sensitive information.

Exploiting CVE-2016-1000127 requires access over the network, without any account, only if a user is tricked into an action.

CIA breakdown of CVE-2016-1000127: confidentiality impact is low, integrity impact is low and availability impact is none.

For CVE-2016-1000127, CVSS v3 gives a base score of 6.1 (medium).

Patch the WordPress plugin AJAX Random Post in the normal cycle, prioritising instances reachable from untrusted networks.
