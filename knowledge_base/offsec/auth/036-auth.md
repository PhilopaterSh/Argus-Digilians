# AUTH — portswigger_labs_sft

- source: portswigger_labs_sft
- class: auth
- cwe: CWE-287

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Password reset poisoning via middleware
Topic: Authentication
Level: Practitioner

Scenario:
This lab is vulnerable to password reset poisoning. The user `carlos` will carelessly click on any links in emails that he receives. To solve the lab, log in to Carlos's account.

 You can log in to your own account using the following credentials: `wiener:peter`. Any emails sent to this account can be read via the email client on the exploit server.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Authentication: "Password reset poisoning via middleware".

## Solution steps

1. With Burp running, investigate the password reset functionality. Observe that a link containing a unique reset token is sent via email.
2. Send the `POST /forgot-password` request to Burp Repeater. Notice that the `X-Forwarded-Host` header is supported and you can use it to point the dynamically generated reset link to an arbitrary domain.
3. Go to the exploit server and make a note of your exploit server URL.
4. Go back to the request in Burp Repeater and add the `X-Forwarded-Host` header with your exploit server URL: `X-Forwarded-Host: YOUR-EXPLOIT-SERVER-ID.exploit-server.net`
5. Change the `username` parameter to `carlos` and send the request.
6. Go to the exploit server and open the access log. You should see a `GET /forgot-password` request, which contains the victim's token as a query parameter. Make a note of this token.
7. Go back to your email client and copy the valid password reset link (not the one that points to the exploit server). Paste this into the browser and change the value of the `temp-forgot-password-token` parameter to the value that you stole from the victim.
8. Load this URL and set a new password for Carlos's account.
9. Log in to Carlos's account using the new password to solve the lab.

## Vulnerability note

Underlying issue: Authentication (CWE-287). Use proven auth libraries, rate-limit and lock out brute force, protect password reset flows, and store credentials with strong hashing.
