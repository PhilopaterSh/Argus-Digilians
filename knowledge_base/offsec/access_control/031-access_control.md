# ACCESS_CONTROL — portswigger_labs_sft

- source: portswigger_labs_sft
- class: access_control
- cwe: CWE-284

## Scenario

I'm stuck on the PortSwigger lab "User ID controlled by request parameter" (Apprentice, Access control vulnerabilities). Here's the scenario:

This lab has a horizontal privilege escalation vulnerability on the user account page.

To solve the lab, obtain the API key for the user `carlos` and submit it as the solution.

You can log in to your own account using the following credentials: `wiener:peter`

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Access control vulnerabilities: "User ID controlled by request parameter".

## Solution steps

1. Log in using the supplied credentials and go to your account page.
2. Note that the URL contains your username in the "id" parameter.
3. Send the request to Burp Repeater.
4. Change the "id" parameter to `carlos`.
5. Retrieve and submit the API key for `carlos`.

## Vulnerability note

Underlying issue: Access control vulnerabilities (CWE-284). Enforce authorization server-side on every request; never rely on hiding UI elements alone.
