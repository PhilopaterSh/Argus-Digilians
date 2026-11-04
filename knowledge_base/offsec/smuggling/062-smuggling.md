# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Help me complete the lab "Exploiting path delimiters for web cache deception" from PortSwigger Web Security Academy. Category: Web cache deception. Difficulty: Practitioner.

To solve the lab, find the API key for the user `carlos`. You can log in to your own account using the following credentials: `wiener:peter`.

We have provided a list of possible delimiter characters to help you solve the lab: Web cache deception lab
 delimiter list.

Required knowledge

 To solve this lab, you'll need to know:

How to identify discrepancies in how the cache and origin server interpret characters as delimiters.
How delimiter discrepancies can be used to exploit a static directory cache rule.
These points are covered in our Web cache deception Academy topic.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Web cache deception: "Exploiting path delimiters for web cache deception".

## Solution steps

1. In Burp's browser, log in to the application using the credentials `wiener:peter`.
2. Notice that the response contains your API key.

## Vulnerability note

Underlying issue: Web cache deception (CWE-444). Do not cache responses that depend on authentication cookies for static-looking paths; normalize cache keys carefully.
