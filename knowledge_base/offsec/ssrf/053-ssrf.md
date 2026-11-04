# SSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: ssrf
- cwe: CWE-918

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Blind SSRF with out-of-band detection
Difficulty: Practitioner
Category: Server-side request forgery (SSRF)

This site uses analytics software which fetches the URL specified in the Referer header when a product page is loaded.

To solve the lab, use this functionality to cause an HTTP request to the public Burp Collaborator server.

Note

 To prevent the Academy platform being used to attack third parties, our firewall blocks interactions between the labs and arbitrary external systems. To solve the lab, you must use Burp Collaborator's default public server.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Server-side request forgery (SSRF): "Blind SSRF with out-of-band detection".

## Solution steps

1. Visit a product, intercept the request in Burp Suite, and send it to Burp Repeater.
2. Go to the Repeater tab. Select the Referer header, right-click and select "Insert Collaborator Payload" to replace the original domain with a Burp Collaborator generated domain. Send the request.
3. Go to the Collaborator tab, and click "Poll now". If you don't see any interactions listed, wait a few seconds and try again, since the server-side command is executed asynchronously.
4. You should see some DNS and HTTP interactions that were initiated by the application as the result of your payload.

## Vulnerability note

Underlying issue: Server-side request forgery (SSRF) (CWE-918). Block requests to internal/metadata IPs, use allowlists for outbound destinations, and avoid passing raw URLs to server-side fetchers.
