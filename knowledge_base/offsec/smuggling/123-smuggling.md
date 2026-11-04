# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Web cache poisoning to exploit a DOM vulnerability via a cache with strict cacheability criteria
Difficulty: Expert
Category: Web cache poisoning

This lab contains a DOM-based vulnerability that can be exploited as part of a web cache poisoning attack. A user visits the home page roughly once a minute. Note that the cache used by this lab has stricter criteria for deciding which responses are cacheable, so you will need to study the cache behavior closely.

To solve the lab, poison the cache with a response that executes `alert(document.cookie)` in the visitor's browser.

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Web cache poisoning: "Web cache poisoning to exploit a DOM vulnerability via a cache with strict cacheability criteria".

## Solution steps

1. With Burp running, open the website's home page.
2. In Burp, go to "Proxy" > "HTTP history" and study the requests and responses that you generated. Find the `GET` request for the home page and send it to Burp Repeater.
3. Use Param Miner to identify that the `X-Forwarded-Host` header is supported.
4. Add a cache buster to the request, as well as the `X-Forwarded-Host` header with an arbitrary hostname, such as `example.com`. Notice that this header overwrites the `data.host` variable, which is passed into the `initGeoLocate()` function.
5. Study the `initGeoLocate()` function in `/resources/js/geolocate.js` and notice that it is vulnerable to DOM-XSS due to the way it handles the incoming JSON data.
6. Go to the exploit server and change the file name to match the path used by the vulnerable response: `/resources/json/geolocate.json`
7. In the head, add the header `Access-Control-Allow-Origin: *` to enable CORS
8. In the body, add a malicious JSON object that matches the one used by the vulnerable website. However, replace the value with a suitable XSS payload, for example: `{ "country": "<img src=1 onerror=alert(document.cookie) />" }`
9. Store the exploit.
10. Back in Burp, find the request for the home page and send it to Burp Repeater.
11. In Burp Repeater, add the following header, remembering to enter your own exploit server ID: `X-Forwarded-Host: YOUR-EXPLOIT-SERVER-ID.exploit-server.net`
12. Send the request until you see your exploit server URL reflected in the response and `X-Cache: hit` in the headers.
13. If this doesn't work, notice that the response contains the `Set-Cookie` header. Responses containing this header are not cacheable on this site. Reload the home page to generate a new request, which should have a session cookie already set.
14. Send this new request to Burp Repeater and repeat the steps above until you successfully poison the cache.
15. To simulate the victim, load the URL in the browser and make sure that the `alert()` fires.
16. Replay the request to keep the cache poisoned until the victim visits the site and the lab is solved

## Vulnerability note

Underlying issue: Web cache poisoning (CWE-444). Only cache on safe keyed inputs; unkeyed headers/cookies that affect responses must not be cached.
