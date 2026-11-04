# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Help me complete the lab "Web cache poisoning via a fat GET request" from PortSwigger Web Security Academy. Category: Web cache poisoning. Difficulty: Practitioner.

This lab is vulnerable to web cache poisoning. It accepts `GET` requests that have a body, but does not include the body in the cache key. A user regularly visits this site's home page using Chrome.

To solve the lab, poison the cache with a response that executes `alert(1)` in the victim's browser.

Provide the ordered solution steps.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Web cache poisoning: "Web cache poisoning via a fat GET request".

## Solution steps

1. Observe that every page imports the script `/js/geolocate.js`, executing the callback function `setCountryCookie()`. Send the request `GET /js/geolocate.js?callback=setCountryCookie` to Burp Repeater.
2. Notice that you can control the name of the function that is called in the response by passing in a duplicate `callback` parameter via the request body. Also notice that the cache key is still derived from the original `callback` parameter in the request line: `GET /js/geolocate.js?callback=setCountryCookie … callback=arbitraryFunction HTTP/1.1 200 OK X-Cache-Key: /js/geolocate.js?callback=setCountryCookie … arbitraryFunction({"country" : "United Kingdom"})`
3. Send the request again, but this time pass in `alert(1)` as the callback function. Check that you can successfully poison the cache.
4. Remove any cache busters and re-poison the cache. The lab will solve when the victim user visits any page containing this resource import URL.

## Vulnerability note

Underlying issue: Web cache poisoning (CWE-444). Only cache on safe keyed inputs; unkeyed headers/cookies that affect responses must not be cached.
