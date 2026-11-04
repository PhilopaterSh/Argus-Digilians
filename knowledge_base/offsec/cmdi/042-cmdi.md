# CMDI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: cmdi
- cwe: CWE-78

## Scenario

Help me complete the lab "Blind OS command injection with time delays" from PortSwigger Web Security Academy. Category: OS command injection. Difficulty: Practitioner.

This lab contains a blind OS command injection vulnerability in the feedback function.

The application executes a shell command containing the user-supplied details. The output from the command is not returned in the response.

To solve the lab, exploit the blind OS command injection vulnerability to cause a 10 second delay.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers OS command injection: "Blind OS command injection with time delays".

## Solution steps

1. Use Burp Suite to intercept and modify the request that submits feedback.
2. Modify the `email` parameter, changing it to: `email=x||ping+-c+10+127.0.0.1||`
3. Observe that the response takes 10 seconds to return.

## Vulnerability note

Underlying issue: OS command injection (CWE-78). Avoid shelling out with user input; use safe APIs with argument arrays and strict allowlists.
