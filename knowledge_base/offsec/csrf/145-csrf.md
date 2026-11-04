# CSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: csrf
- cwe: CWE-352

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: SameSite Strict bypass via client-side redirect
Difficulty: Practitioner
Category: Cross-site request forgery (CSRF)

This lab's change email function is vulnerable to CSRF. To solve the lab, perform a CSRF attack that changes the victim's email address. You should use the provided exploit server to host your attack.

You can log in to your own account using the following credentials: `wiener:peter`

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Cross-site request forgery (CSRF): "SameSite Strict bypass via client-side redirect".

## Solution steps

1. In Burp's browser, log in to your own account and change your email address.
2. In Burp, go to the Proxy > HTTP history tab.
3. Study the `POST /my-account/change-email` request and notice that this doesn't contain any unpredictable tokens, so may be vulnerable to CSRF if you can bypass any SameSite cookie restrictions.
4. Look at the response to your `POST /login` request. Notice that the website explicitly specifies `SameSite=Strict` when setting session cookies. This prevents the browser from including these cookies in cross-site requests.

## Vulnerability note

Underlying issue: Cross-site request forgery (CSRF) (CWE-352). Prevent CSRF with anti-CSRF tokens, SameSite cookies, and avoiding cookie-only auth for state-changing requests.
