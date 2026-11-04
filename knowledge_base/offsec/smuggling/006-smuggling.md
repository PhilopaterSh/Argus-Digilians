# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Cache key injection
Topic: Web cache poisoning
Level: Expert

Scenario:
This lab contains multiple independent vulnerabilities, including cache key injection. A user regularly visits this site's home page using Chrome.

To solve the lab, combine the vulnerabilities to execute `alert(1)` in the victim's browser. Note that you will need to make use of the `Pragma: x-get-cache-key` header in order to solve this lab.

## Analysis / Response

This PortSwigger Web Security Academy lab (Expert) covers Web cache poisoning: "Cache key injection".

## Solution steps

1. Observe that the redirect at `/login` excludes the parameter `utm_content` from the cache key using a flawed regex. This allows you append arbitrary unkeyed content to the `lang` parameter: `/login?lang=en?utm_content=anything`
2. Observe that the page at `/login/` has an import from `/js/localize.js`. This is vulnerable to client-side parameter pollution via the `lang` parameter because it doesn't URL-encode the value.
3. Observe that the login page references an endpoint at `/js/localize.js` that is vulnerable to response header injection via the `Origin` request header, provided the `cors` parameter is set to `1`.
4. Use the `Pragma: x-get-cache-key` header to identify that the server is vulnerable to cache key injection, meaning the header injection can be triggered via a crafted URL.
5. Combine these four behaviors by poisoning the cache with following two requests: `GET /js/localize.js?lang=en?utm_content=z&cors=1&x=1 HTTP/2 Origin: x%0d%0aContent-Length:%208%0d%0a%0d%0aalert(1)$$$$ GET /login?lang=en?utm_content=x%26cors=1%26x=1$$origin=x%250d%250aContent-Length:%208%250d%250a%250d%250aalert(1)$$%23 HTTP/2` Note that the injected origin header is lower case to comply with the HTTP/2 specification.
6. This will poison `/login?lang=en` such that it redirects to a login page with a poisoned localization import that executes `alert(1)`, solving the lab.

## Vulnerability note

Underlying issue: Web cache poisoning (CWE-444). Only cache on safe keyed inputs; unkeyed headers/cookies that affect responses must not be cached.
