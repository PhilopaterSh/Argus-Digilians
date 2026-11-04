# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-1336

## Scenario

Give me a rundown of Server Side Template Injection - PHP for Server Side Template Injection: when to use it and the payloads involved.

## Analysis / Response

**Server Side Template Injection - PHP** — this technique applies to Server Side Template Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

> Server-Side Template Injection (SSTI)  is a vulnerability that occurs when an attacker can inject malicious input into a server-side template, causing the template engine to execute arbitrary commands on the server. In PHP, SSTI can arise when user input is embedded within templates rendered by templating engines like Smarty, Twig, or even within plain PHP templates, without proper sanitization or validation.
