# ACCESS_CONTROL — portswigger_labs_sft

- source: portswigger_labs_sft
- class: access_control
- cwe: CWE-284

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: User ID controlled by request parameter, with unpredictable user IDs
Topic: Access control vulnerabilities
Level: Apprentice

Scenario:
This lab has a horizontal privilege escalation vulnerability on the user account page, but identifies users with GUIDs.

To solve the lab, find the GUID for `carlos`, then submit his API key as the solution.

You can log in to your own account using the following credentials: `wiener:peter`

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Access control vulnerabilities: "User ID controlled by request parameter, with unpredictable user IDs".

## Solution steps

1. Find a blog post by `carlos`.
2. Click on `carlos` and observe that the URL contains his user ID. Make a note of this ID.
3. Log in using the supplied credentials and access your account page.
4. Change the "id" parameter to the saved user ID.
5. Retrieve and submit the API key.

## Vulnerability note

Underlying issue: Access control vulnerabilities (CWE-284). Enforce authorization server-side on every request; never rely on hiding UI elements alone.
