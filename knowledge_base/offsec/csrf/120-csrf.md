# CSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: csrf
- cwe: CWE-352

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: CSRF where Referer validation depends on header being present
Topic: Cross-site request forgery (CSRF)
Level: Practitioner

Scenario:
This lab's email change functionality is vulnerable to CSRF. It attempts to block cross domain requests but has an insecure fallback.

To solve the lab, use your exploit server to host an HTML page that uses a CSRF attack to change the viewer's email address.

You can log in to your own account using the following credentials: `wiener:peter`

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Cross-site request forgery (CSRF): "CSRF where Referer validation depends on header being present".

## Solution steps

1. Open Burp's browser and log in to your account. Submit the "Update email" form, and find the resulting request in your Proxy history.
2. Send the request to Burp Repeater and observe that if you change the domain in the Referer HTTP header then the request is rejected.
3. Delete the Referer header entirely and observe that the request is now accepted.
4. Create and host a proof of concept exploit as described in the solution to the CSRF vulnerability with no defenses lab. Include the following HTML to suppress the Referer header: `<meta name="referrer" content="no-referrer">`
5. Change the email address in your exploit so that it doesn't match your own.
6. Store the exploit, then click "Deliver to victim" to solve the lab.

## Vulnerability note

Underlying issue: Cross-site request forgery (CSRF) (CWE-352). Prevent CSRF with anti-CSRF tokens, SameSite cookies, and avoiding cookie-only auth for state-changing requests.
