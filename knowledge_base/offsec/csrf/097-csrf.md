# CSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: csrf
- cwe: CWE-352

## Scenario

Scenario framing — PortSwigger "CSRF where token is tied to non-session cookie" (Cross-site request forgery (CSRF), Practitioner):
This lab's email change functionality is vulnerable to CSRF. It uses tokens to try to prevent CSRF attacks, but they aren't fully integrated into the site's session handling system.

To solve the lab, use your exploit server to host an HTML page that uses a CSRF attack to change the viewer's email address.

You have two accounts on the application that you can use to help design your attack. The credentials are as follows:

`wiener:peter`
`carlos:montoya`

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Cross-site request forgery (CSRF): "CSRF where token is tied to non-session cookie".

## Solution steps

1. Open Burp's browser and log in to your account. Submit the "Update email" form, and find the resulting request in your Proxy history.
2. Send the request to Burp Repeater and observe that changing the `session` cookie logs you out, but changing the `csrfKey` cookie merely results in the CSRF token being rejected. This suggests that the `csrfKey` cookie may not be strictly tied to the session.
3. Open a private/incognito browser window, log in to your other account, and send a fresh update email request into Burp Repeater.
4. Observe that if you swap the `csrfKey` cookie and `csrf` parameter from the first account to the second account, the request is accepted.
5. Close the Repeater tab and incognito browser.
6. Back in the original browser, perform a search, send the resulting request to Burp Repeater, and observe that the search term gets reflected in the Set-Cookie header. Since the search function has no CSRF protection, you can use this to inject cookies into the victim user's browser.
7. Create a URL that uses this vulnerability to inject your `csrfKey` cookie into the victim's browser: `/?search=test%0d%0aSet-Cookie:%20csrfKey=YOUR-KEY%3b%20SameSite=None`
8. Create and host a proof of concept exploit as described in the solution to the CSRF vulnerability with no defenses lab, ensuring that you include your CSRF token. The exploit should be created from the email change request.
9. Remove the auto-submit `<script>` block, and instead add the following code to inject the cookie: `<img src="https://YOUR-LAB-ID.web-security-academy.net/?search=test%0d%0aSet-Cookie:%20csrfKey=YOUR-KEY%3b%20SameSite=None" onerror="document.forms[0].submit()">`
10. Change the email address in your exploit so that it doesn't match your own.
11. Store the exploit, then click "Deliver to victim" to solve the lab.

## Vulnerability note

Underlying issue: Cross-site request forgery (CSRF) (CWE-352). Prevent CSRF with anti-CSRF tokens, SameSite cookies, and avoiding cookie-only auth for state-changing requests.
