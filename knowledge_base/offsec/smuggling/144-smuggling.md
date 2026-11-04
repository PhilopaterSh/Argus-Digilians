# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: HTTP/2 request smuggling via CRLF injection
Topic: HTTP request smuggling
Level: Practitioner

Scenario:
This lab is vulnerable to request smuggling because the front-end server downgrades HTTP/2 requests and fails to adequately sanitize incoming headers.

To solve the lab, use an HTTP/2-exclusive request smuggling vector to gain access to another user's account. The victim accesses the home page every 15 seconds.

If you're not familiar with Burp's exclusive features for HTTP/2 testing, please refer to the documentation for details on how to use them.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "HTTP/2 request smuggling via CRLF injection".

## Solution steps

1. In Burp's browser, use the lab's search function a couple of times and observe that the website records your recent search history. Send the most recent `POST /` request to Burp Repeater and remove your session cookie before resending the request. Notice that your search history is reset, confirming that it's tied to your session cookie.
2. Expand the Inspector's Request Attributes section and make sure the protocol is set to HTTP/2.
3. Using the Inspector, add an arbitrary header to the request. Append the sequence `\r\n` to the header's value, followed by the `Transfer-Encoding: chunked` header: Name `foo` Value `bar\r\n Transfer-Encoding: chunked`
4. In the body, attempt to smuggle an arbitrary prefix as follows: `0 SMUGGLED` Observe that every second request you send receives a 404 response, confirming that you have caused the back-end to append the subsequent request to the smuggled prefix
5. Change the body of the request to the following: `0 POST / HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net Cookie: session=YOUR-SESSION-COOKIE Content-Length: 800 search=x`
6. Send the request, then immediately refresh the page in the browser. The next step depends on which response you receive: If you got lucky with your timing, you may see a `404 Not Found` response. In this case, refresh the page again and move on to the next step. If you instead see the search results page, observe that the start of your request is reflected on the page because it was appended to the `search=x` parameter in the smuggled prefix. In this case, send the request again, but this time wait for 15 seconds before refreshing the page. If you see a 404 response, just refresh the page again.
7. Check the recent searches list. If it contains a `GET` request, this is the start of the victim user's request and includes their session cookie. If you instead see your own `POST` request, you refreshed the page too early. Try again until you have successfully stolen the victim's session cookie.
8. In Burp Repeater, send a request for the home page using the stolen session cookie to solve the lab.

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
