# CSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: csrf
- cwe: CWE-352

## Scenario

PortSwigger lab: "SameSite Lax bypass via method override". This lab's change email function is vulnerable to CSRF. To solve the lab, perform a CSRF attack that changes the victim's email address. You should use the provided exploit server to host your attack.

You can log in to your own account using the following credentials: `wiener:peter`

Note

 The default SameSite restrictions differ between browsers. As the victim uses Chrome, we recommend also using Chrome (or Burp's built-in Chromium browser) to test your exploit.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Cross-site request forgery (CSRF): "SameSite Lax bypass via method override".

## Solution steps

1. In Burp's browser, log in to your own account and change your email address.
2. In Burp, go to the Proxy > HTTP history tab.
3. Study the `POST /my-account/change-email` request and notice that this doesn't contain any unpredictable tokens, so may be vulnerable to CSRF if you can bypass the SameSite cookie restrictions.
4. Look at the response to your `POST /login` request. Notice that the website doesn't explicitly specify any SameSite restrictions when setting session cookies. As a result, the browser will use the default `Lax` restriction level.
5. Recognize that this means the session cookie will be sent in cross-site `GET` requests, as long as they involve a top-level navigation.

## Vulnerability note

Underlying issue: Cross-site request forgery (CSRF) (CWE-352). Prevent CSRF with anti-CSRF tokens, SameSite cookies, and avoiding cookie-only auth for state-changing requests.
