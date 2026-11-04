# AUTH — portswigger_labs_sft

- source: portswigger_labs_sft
- class: auth
- cwe: CWE-287

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Password reset broken logic
Difficulty: Apprentice
Category: Authentication

This lab's password reset functionality is vulnerable. To solve the lab, reset Carlos's password then log in and access his "My account" page.

Your credentials: `wiener:peter`

 Victim's username: `carlos`

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Authentication: "Password reset broken logic".

## Solution steps

1. With Burp running, click the Forgot your password? link and enter your own username.
2. Click the Email client button to view the password reset email that was sent. Click the link in the email and reset your password to whatever you want.
3. In Burp, go to Proxy > HTTP history and study the requests and responses for the password reset functionality. Observe that the reset token is provided as a URL query parameter in the reset email. Notice that when you submit your new password, the `POST /forgot-password?temp-forgot-password-token` request contains the username as hidden input. Send this request to Burp Repeater.
4. In Burp Repeater, observe that the password reset functionality still works even if you delete the value of the `temp-forgot-password-token` parameter in both the URL and request body. This confirms that the token is not being checked when you submit the new password.
5. In the browser, request a new password reset and change your password again. Send the `POST /forgot-password?temp-forgot-password-token` request to Burp Repeater again.
6. In Burp Repeater, delete the value of the `temp-forgot-password-token` parameter in both the URL and request body. Change the `username` parameter to `carlos`. Set the new password to whatever you want and send the request.
7. In the browser, log in to Carlos's account using the new password you just set. Click My account to solve the lab.

## Vulnerability note

Underlying issue: Authentication (CWE-287). Use proven auth libraries, rate-limit and lock out brute force, protect password reset flows, and store credentials with strong hashing.
