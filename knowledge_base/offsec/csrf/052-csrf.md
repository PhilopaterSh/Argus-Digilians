# CSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: csrf
- cwe: CWE-352

## Scenario

How do I test for CSRF: 6. Regenerate token when on an in-scope web application?

## Analysis / Response

Based on Abhishek Pawar notes — CSRF Report (6. Regenerate token when:):

6. Regenerate token when:
         • User logs in
         • User logs out
         • Session is rotated
   7. Use SameSite=Lax with no GET state-changing request in the application.
Note: Cross-Site Scripting (XSS) is the most critical threat to CSRF defenses, as successful
XSS execution allows an attacker to bypass most CSRF mitigation techniques by operating
within the same origin and accessing CSRF tokens directly.

3.1.3 Transmitting CSRF Tokens in Synchronized Patterns
Server → Client via hidden form fields (response payloads) or JSON response.

Client → Server
There are two ways to send CSRF token from client to server.

                                                                                       pg. 12

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
