# UNCATEGORIZED — portswigger_labs_sft

- source: portswigger_labs_sft
- class: uncategorized

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Scanning non-standard data structures
Difficulty: Practitioner
Category: Essential skills

This lab contains a vulnerability that is difficult to find manually. It is located in a non-standard data structure.

To solve the lab, use Burp Scanner's Scan selected insertion point feature to identify the vulnerability, then manually exploit it and delete `carlos`.

You can log in to your own account with the following credentials: `wiener:peter`

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Essential skills: "Scanning non-standard data structures".

## Solution steps

1. Log in to your account with the provided credentials.
2. In Burp, go to the Proxy > HTTP history tab.
3. Find the `GET /my-account?id=wiener` request, which contains your new authenticated session cookie.
4. Study the session cookie and notice that it contains your username in cleartext, followed by a token of some kind. These are separated by a colon, which suggests that the application may treat the cookie value as two distinct inputs.
5. Select the first part of the session cookie, the cleartext `wiener`.
6. Right-click and select Scan selected insertion point, then click OK.
7. Go to the Dashboard and wait for the scan to complete.

## Vulnerability note

Underlying issue: Essential skills. Practice methodical recon, proxy usage, and careful request manipulation in authorized labs only.
