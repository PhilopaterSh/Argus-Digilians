# PATHTRAVER — portswigger_labs_sft

- source: portswigger_labs_sft
- class: pathtraver
- cwe: CWE-22

## Scenario

Help me complete the lab "File path traversal, traversal sequences blocked with absolute path bypass" from PortSwigger Web Security Academy. Category: Path traversal. Difficulty: Practitioner.

This lab contains a path traversal vulnerability in the display of product images.

The application blocks traversal sequences but treats the supplied filename as being relative to a default working directory.

To solve the lab, retrieve the contents of the `/etc/passwd` file.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Path traversal: "File path traversal, traversal sequences blocked with absolute path bypass".

## Solution steps

1. Use Burp Suite to intercept and modify a request that fetches a product image.
2. Modify the `filename` parameter, giving it the value `/etc/passwd`.
3. Observe that the response contains the contents of the `/etc/passwd` file.

## Vulnerability note

Underlying issue: Path traversal (CWE-22). Canonicalize and validate paths against an allowlisted base directory; reject .. and absolute paths.
