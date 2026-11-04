# CMDI — portswigger_labs_sft

- source: portswigger_labs_sft
- class: cmdi
- cwe: CWE-78

## Scenario

Scenario framing — PortSwigger "OS command injection, simple case" (OS command injection, Apprentice):
This lab contains an OS command injection vulnerability in the product stock checker.

The application executes a shell command containing user-supplied product and store IDs, and returns the raw output from the command in its response.

To solve the lab, execute the `whoami` command to determine the name of the current user.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers OS command injection: "OS command injection, simple case".

## Solution steps

1. Use Burp Suite to intercept and modify a request that checks the stock level.
2. Modify the `storeID` parameter, giving it the value `1|whoami`.
3. Observe that the response contains the name of the current user.

## Vulnerability note

Underlying issue: OS command injection (CWE-78). Avoid shelling out with user input; use safe APIs with argument arrays and strict allowlists.
