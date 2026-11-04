# ACCESS_CONTROL — portswigger_labs_sft

- source: portswigger_labs_sft
- class: access_control
- cwe: CWE-284

## Scenario

PortSwigger lab: "User role controlled by request parameter". This lab has an admin panel at `/admin`, which identifies administrators using a forgeable cookie.

Solve the lab by accessing the admin panel and using it to delete the user `carlos`.

You can log in to your own account using the following credentials: `wiener:peter`

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Access control vulnerabilities: "User role controlled by request parameter".

## Solution steps

1. Browse to `/admin` and observe that you can't access the admin panel.
2. Browse to the login page.
3. In Burp Proxy, turn interception on and enable response interception.
4. Complete and submit the login page, and forward the resulting request in Burp.
5. Observe that the response sets the cookie `Admin=false`. Change it to `Admin=true`.
6. Load the admin panel and delete `carlos`.

## Vulnerability note

Underlying issue: Access control vulnerabilities (CWE-284). Enforce authorization server-side on every request; never rely on hiding UI elements alone.
