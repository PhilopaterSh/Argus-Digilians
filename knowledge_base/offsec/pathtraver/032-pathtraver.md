# PATHTRAVER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: pathtraver
- cwe: CWE-22

## Scenario

Scenario framing — PortSwigger "File path traversal, simple case" (Path traversal, Apprentice):
This lab contains a path traversal vulnerability in the display of product images.

To solve the lab, retrieve the contents of the `/etc/passwd` file.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Path traversal: "File path traversal, simple case".

## Solution steps

1. Use Burp Suite to intercept and modify a request that fetches a product image.
2. Modify the `filename` parameter, giving it the value: `../../../etc/passwd`
3. Observe that the response contains the contents of the `/etc/passwd` file.

## Vulnerability note

Underlying issue: Path traversal (CWE-22). Canonicalize and validate paths against an allowlisted base directory; reject .. and absolute paths.
