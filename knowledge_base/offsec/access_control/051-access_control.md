# ACCESS_CONTROL — portswigger_labs_sft

- source: portswigger_labs_sft
- class: access_control
- cwe: CWE-284

## Scenario

Scenario framing — PortSwigger "Referer-based access control" (Access control vulnerabilities, Practitioner):
This lab controls access to certain admin functionality based on the Referer header. You can familiarize yourself with the admin panel by logging in using the credentials `administrator:admin`.

To solve the lab, log in using the credentials `wiener:peter` and exploit the flawed access controls to promote yourself to become an administrator.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Access control vulnerabilities: "Referer-based access control".

## Solution steps

1. Log in using the admin credentials.
2. Browse to the admin panel, promote `carlos`, and send the HTTP request to Burp Repeater.
3. Open a private/incognito browser window, and log in with the non-admin credentials.
4. Browse to `/admin-roles?username=carlos&action=upgrade` and observe that the request is treated as unauthorized due to the absent Referer header.
5. Copy the non-admin user's session cookie into the existing Burp Repeater request, change the username to yours, and replay it.

## Vulnerability note

Underlying issue: Access control vulnerabilities (CWE-284). Enforce authorization server-side on every request; never rely on hiding UI elements alone.
