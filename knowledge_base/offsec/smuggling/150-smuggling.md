# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

I'm stuck on the PortSwigger lab "Exploiting exact-match cache rules for web cache deception" (Expert, Web cache deception). Here's the scenario:

To solve the lab, change the email address for the user `administrator`. You can log in to your own account using the following credentials: `wiener:peter`.

We have provided a list of possible delimiter characters to help you solve the lab: Web cache deception lab
 delimiter list.

Required knowledge

 To solve this lab, you'll need to know:

How to identify exact-match file name cache rules.
How to exploit exact-match file name cache rules using delimiter and normalization discrepancies.
How to construct a CSRF attack. For more information, see the Cross-site request forgery Academy topic.
These points are covered in our Web cache deception Academy topic.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Web cache deception: "Exploiting exact-match cache rules for web cache deception".

## Solution steps

1. In Burp's browser, log in to the application using the credentials `wiener:peter`, then change your email address.
2. In Proxy > HTTP history, notice that the email change submission form in the `/my-account` response contains a CSRF token as a hidden parameter.

## Vulnerability note

Underlying issue: Web cache deception (CWE-444). Do not cache responses that depend on authentication cookies for static-looking paths; normalize cache keys carefully.
