# AUTH — portswigger_labs_sft

- source: portswigger_labs_sft
- class: auth
- cwe: CWE-287

## Scenario

PortSwigger lab: "2FA broken logic". This lab's two-factor authentication is vulnerable due to its flawed logic. To solve the lab, access Carlos's account page.

Your credentials: `wiener:peter`

 Victim's username: `carlos`

You also have access to the email server to receive your 2FA verification code.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Authentication: "2FA broken logic".

## Solution steps

1. With Burp running, log in to your own account and investigate the 2FA verification process. Notice that in the `POST /login2` request, the `verify` parameter is used to determine which user's account is being accessed.
2. Log out of your account.
3. Send the `GET /login2` request to Burp Repeater. Change the value of the `verify` parameter to `carlos` and send the request. This ensures that a temporary 2FA code is generated for Carlos.
4. Go to the login page and enter your username and password. Then, submit an invalid 2FA code.
5. Send the `POST /login2` request to Burp Intruder.
6. In Burp Intruder, set the `verify` parameter to `carlos` and add a payload position to the `mfa-code` parameter. Brute-force the verification code.
7. Load the 302 response in the browser.
8. Click My account to solve the lab.

## Vulnerability note

Underlying issue: Authentication (CWE-287). Use proven auth libraries, rate-limit and lock out brute force, protect password reset flows, and store credentials with strong hashing.
