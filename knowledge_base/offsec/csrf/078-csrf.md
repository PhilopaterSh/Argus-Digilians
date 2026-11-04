# CSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: csrf
- cwe: CWE-352

## Scenario

Help me complete the lab "CSRF where token is duplicated in cookie" from PortSwigger Web Security Academy. Category: Cross-site request forgery (CSRF). Difficulty: Practitioner.

This lab's email change functionality is vulnerable to CSRF. It attempts to use the insecure "double submit" CSRF prevention technique.

To solve the lab, use your exploit server to host an HTML page that uses a CSRF attack to change the viewer's email address.

You can log in to your own account using the following credentials: `wiener:peter`

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Cross-site request forgery (CSRF): "CSRF where token is duplicated in cookie".

## Solution steps

1. Open Burp's browser and log in to your account. Submit the "Update email" form, and find the resulting request in your Proxy history.
2. Send the request to Burp Repeater and observe that the value of the `csrf` body parameter is simply being validated by comparing it with the `csrf` cookie.
3. Perform a search, send the resulting request to Burp Repeater, and observe that the search term gets reflected in the Set-Cookie header. Since the search function has no CSRF protection, you can use this to inject cookies into the victim user's browser.
4. Create a URL that uses this vulnerability to inject a fake `csrf` cookie into the victim's browser: `/?search=test%0d%0aSet-Cookie:%20csrf=fake%3b%20SameSite=None`
5. Create and host a proof of concept exploit as described in the solution to the CSRF vulnerability with no defenses lab, ensuring that your CSRF token is set to "fake". The exploit should be created from the email change request.
6. Remove the auto-submit `<script>` block and instead add the following code to inject the cookie and submit the form: `<img src="https://YOUR-LAB-ID.web-security-academy.net/?search=test%0d%0aSet-Cookie:%20csrf=fake%3b%20SameSite=None" onerror="document.forms[0].submit();"/>`
7. Change the email address in your exploit so that it doesn't match your own.
8. Store the exploit, then click "Deliver to victim" to solve the lab.

## Vulnerability note

Underlying issue: Cross-site request forgery (CSRF) (CWE-352). Prevent CSRF with anti-CSRF tokens, SameSite cookies, and avoiding cookie-only auth for state-changing requests.
