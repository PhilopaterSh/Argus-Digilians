# ACCESS_CONTROL — portswigger_labs_sft

- source: portswigger_labs_sft
- class: access_control
- cwe: CWE-284

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Multi-step process with no access control on one step
Topic: Access control vulnerabilities
Level: Practitioner

Scenario:
This lab has an admin panel with a flawed multi-step process for changing a user's role. You can familiarize yourself with the admin panel by logging in using the credentials `administrator:admin`.

To solve the lab, log in using the credentials `wiener:peter` and exploit the flawed access controls to promote yourself to become an administrator.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Access control vulnerabilities: "Multi-step process with no access control on one step".

## Solution steps

1. Log in using the admin credentials.
2. Browse to the admin panel, promote `carlos`, and send the confirmation HTTP request to Burp Repeater.
3. Open a private/incognito browser window, and log in with the non-admin credentials.
4. Copy the non-admin user's session cookie into the existing Repeater request, change the username to yours, and replay it.

## Vulnerability note

Underlying issue: Access control vulnerabilities (CWE-284). Enforce authorization server-side on every request; never rely on hiding UI elements alone.
