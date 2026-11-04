# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Scenario framing — PortSwigger "Exploiting path mapping for web cache deception" (Web cache deception, Apprentice):
To solve the lab, find the API key for the user `carlos`. You can log in to your own account using the following credentials: `wiener:peter`.

Required knowledge

 To solve this lab, you'll need to know:

How regex endpoints map URL paths to resources.
How to detect and exploit discrepancies in the way the cache and origin server map URL paths.
These points are covered in our Web cache deception Academy topic.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Web cache deception: "Exploiting path mapping for web cache deception".

## Solution steps

1. In Burp's browser, log in to the application using the credentials `wiener:peter`.
2. Notice that the response contains your API key.

## Vulnerability note

Underlying issue: Web cache deception (CWE-444). Do not cache responses that depend on authentication cookies for static-looking paths; normalize cache keys carefully.
