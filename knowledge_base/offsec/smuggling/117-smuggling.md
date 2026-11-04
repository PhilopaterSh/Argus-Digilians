# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

PortSwigger lab: "URL normalization". This lab contains an XSS vulnerability that is not directly exploitable due to browser URL-encoding.

To solve the lab, take advantage of the cache's normalization process to exploit this vulnerability. Find the XSS vulnerability and inject a payload that will execute `alert(1)` in the victim's browser. Then, deliver the malicious URL to the victim.

Walk me through how to solve it.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Web cache poisoning: "URL normalization".

## Solution steps

1. In Burp Repeater, browse to any non-existent path, such as `GET /random`. Notice that the path you requested is reflected in the error message.
2. Add a suitable reflected XSS payload to the request line: `GET /random</p><script>alert(1)</script><p>foo`
3. Notice that if you request this URL in the browser, the payload doesn't execute because it is URL-encoded.
4. In Burp Repeater, poison the cache with your payload and then immediately load the URL in the browser. This time, the `alert()` is executed because the browser's encoded payload was URL-decoded by the cache, causing a cache hit with the earlier request.
5. Re-poison the cache then immediately go to the lab and click "Deliver link to victim". Submit your malicious URL. The lab will be solved when the victim visits the link.

## Vulnerability note

Underlying issue: Web cache poisoning (CWE-444). Only cache on safe keyed inputs; unkeyed headers/cookies that affect responses must not be cached.
