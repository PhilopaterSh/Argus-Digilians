# SSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: ssrf
- cwe: CWE-918

## Scenario

Help me complete the lab "Basic SSRF against the local server" from PortSwigger Web Security Academy. Category: Server-side request forgery (SSRF). Difficulty: Apprentice.

This lab has a stock check feature which fetches data from an internal system.

To solve the lab, change the stock check URL to access the admin interface at `http://localhost/admin` and delete the user `carlos`.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Server-side request forgery (SSRF): "Basic SSRF against the local server".

## Solution steps

1. Browse to `/admin` and observe that you can't directly access the admin page.
2. Visit a product, click "Check stock", intercept the request in Burp Suite, and send it to Burp Repeater.
3. Change the URL in the `stockApi` parameter to `http://localhost/admin`. This should display the administration interface.
4. Read the HTML to identify the URL to delete the target user, which is: `http://localhost/admin/delete?username=carlos`
5. Submit this URL in the `stockApi` parameter, to deliver the SSRF attack.

## Vulnerability note

Underlying issue: Server-side request forgery (SSRF) (CWE-918). Block requests to internal/metadata IPs, use allowlists for outbound destinations, and avoid passing raw URLs to server-side fetchers.
