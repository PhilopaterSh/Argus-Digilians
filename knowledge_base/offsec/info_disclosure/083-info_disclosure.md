# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

How do I test for Web Application Hacker's Handbook 2e — When this kind of error reporting functionality is present in live production on an in-scope web application?

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (When this kind of error reporting functionality is present in live production):

When this kind of error reporting functionality is present in live production
               code, it may signify a critical weakness in the application’s security. You should
               review it closely to identify any items that can be used to further advance your
               attack, and any ways in which you can supply crafted input to manipulate the
               application’s state and control the information retrieved.

               Server and Database Messages
               Informative error messages are often returned not by the application itself but
               by some back-end component such as a database, mail server, or SOAP server. If
               a completely unhandled error occurs, the application typically responds with an

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
