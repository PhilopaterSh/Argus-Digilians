# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Explain Web Application Hacker's Handbook 2e — Handle Credentials Secretively with payloads/commands where the material provides them (authorized testing only).

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Handle Credentials Secretively):

Handle Credentials Secretively
                   n   All credentials should be created, stored, and transmitted in a manner
                       that does not lead to unauthorized disclosure.
                   n   All client-server communications should be protected using a well-
                       established cryptographic technology, such as SSL. Custom solutions
                       for protecting data in transit are neither necessary nor desirable.
                   n   If it is considered preferable to use HTTP for the unauthenticated areas of
                       the application, ensure that the login form itself is loaded using HTTPS,
                       rather than switching to HTTPS at the point of the login submission.
                   n   Only POST requests should be used to transmit credentials to the server.
                       Credentials should never be placed in URL parameters or cookies (even
                       ephemeral ones). Credentials should never be transmitted back to the
                       client, even in parameters to a redirect.
                   n   All server-side application components should store credentials in a man-
                       ner that does not allow their original values to be easily recovered, even
                       by an attacker who gains full access to all the relevant data within the

c06.indd 192                                                                                           8/19/2011 12:06:41 PM

                                                               Stuttard c06.indd V3 - 07/22/2011 Page 193
