# SSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: ssrf
- cwe: CWE-918

## Scenario

I'm stuck on the PortSwigger lab "SSRF with blacklist-based input filter" (Practitioner, Server-side request forgery (SSRF)). Here's the scenario:

This lab has a stock check feature which fetches data from an internal system.

To solve the lab, change the stock check URL to access the admin interface at `http://localhost/admin` and delete the user `carlos`.

The developer has deployed two weak anti-SSRF defenses that you will need to bypass.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Server-side request forgery (SSRF): "SSRF with blacklist-based input filter".

## Solution steps

1. Visit a product, click "Check stock", intercept the request in Burp Suite, and send it to Burp Repeater.
2. Change the URL in the `stockApi` parameter to `http://127.0.0.1/` and observe that the request is blocked.
3. Bypass the block by changing the URL to: `http://127.1/`
4. Change the URL to `http://127.1/admin` and observe that the URL is blocked again.
5. Obfuscate the "a" by double-URL encoding it to %2561 to access the admin interface and delete the target user.

## Vulnerability note

Underlying issue: Server-side request forgery (SSRF) (CWE-918). Block requests to internal/metadata IPs, use allowlists for outbound destinations, and avoid passing raw URLs to server-side fetchers.
