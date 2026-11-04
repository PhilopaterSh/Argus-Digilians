# SSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: ssrf
- cwe: CWE-918

## Scenario

PortSwigger lab: "Basic SSRF against another back-end system". This lab has a stock check feature which fetches data from an internal system.

To solve the lab, use the stock check functionality to scan the internal `192.168.0.X` range for an admin interface on port
 `8080`, then use it to delete the user `carlos`.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers Server-side request forgery (SSRF): "Basic SSRF against another back-end system".

## Solution steps

1. Visit a product, click Check stock, intercept the request in Burp Suite, and send it to Burp Intruder.
2. Change the `stockApi` parameter to `http://192.168.0.1:8080/admin` then highlight the final octet of the IP address (the number `1`) and click Add §.
3. In the Payloads side panel, change the payload type to Numbers, and enter 1, 255, and 1 in the From and To and Step boxes respectively.
4. Click Start attack.
5. Click on the Status column to sort it by status code ascending. You should see a single entry with a status of `200`, showing an admin interface.
6. Click on this request, send it to Burp Repeater, and change the path in the `stockApi` to: `/admin/delete?username=carlos`

## Vulnerability note

Underlying issue: Server-side request forgery (SSRF) (CWE-918). Block requests to internal/metadata IPs, use allowlists for outbound destinations, and avoid passing raw URLs to server-side fetchers.
