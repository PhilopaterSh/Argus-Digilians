# CRYPTO_WEAK — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: crypto_weak
- cwe: CWE-327

## Scenario

What controls mitigate common web security protocols (TLS, encoding, crypto basics) effectively (angle: TLS basics for testers) [Ch 1: Common Security Protocols]?

## Analysis / Response

## Overview
During authorized testing, consider an example in which a web page running at origin A sends an HTTP request to origin B impersonating the user and loads up the page, which may include Cross-Site Request Forgery (CSRF) tokens, and then they can be used to mount a CSRF attack. So the same-origin policy basically makes calling separate origin documents through AJAX functions a problem.

## Key points
However, in the next section, you'll attempt to dig deeper into this. CORS CORS allows cross-domain HTTP data exchange, which means a page running at origin A can send/receive data from a server at origin B. CORS is abundantly used in web applications where web fonts, CSS, documents, and so on are loaded from different origins, which may not be of the origin where the resources are actually stored. When reviewing an application, most content delivery networks (CDNs) which provide resource-hosting functionality typically allow any website or origin to interact with themselves.

## Additional notes
When reviewing an application, cORS works by adding a new HTTP header that allows the web server to speak up a list of whitelisted domains that are allowed to connect and interact with the server. This thing is also browser enforced; the browser reads the header and processes accordingly.

## Remediation ideas
1. Prefer fixing the root cause: When reviewing an application, cORS works by adding a new HTTP header that allows the web server to speak up a list of whitelisted domains that are allowed to connect and interact with the server.
2. Prefer fixing the root cause: This thing is also browser enforced; the browser reads the header and processes accordingly.

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
