# PATHTRAVER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: pathtraver
- cwe: CWE-22

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: File path traversal, traversal sequences stripped with superfluous URL-decode
Difficulty: Practitioner
Category: Path traversal

This lab contains a path traversal vulnerability in the display of product images.

The application blocks input containing path traversal sequences. It then performs a URL-decode of the input before using it.

To solve the lab, retrieve the contents of the `/etc/passwd` file.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Path traversal: "File path traversal, traversal sequences stripped with superfluous URL-decode".

## Solution steps

1. Use Burp Suite to intercept and modify a request that fetches a product image.
2. Modify the `filename` parameter, giving it the value: `..%252f..%252f..%252fetc/passwd`
3. Observe that the response contains the contents of the `/etc/passwd` file.

## Vulnerability note

Underlying issue: Path traversal (CWE-22). Canonicalize and validate paths against an allowlisted base directory; reject .. and absolute paths.
