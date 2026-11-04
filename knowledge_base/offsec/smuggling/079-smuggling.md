# SMUGGLING — portswigger_labs_sft

- source: portswigger_labs_sft
- class: smuggling
- cwe: CWE-444

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Response queue poisoning via H2.TE request smuggling
Difficulty: Practitioner
Category: HTTP request smuggling

This lab is vulnerable to request smuggling because the front-end server downgrades HTTP/2 requests even if they have an ambiguous length.

To solve the lab, delete the user `carlos` by using response queue poisoning to break into the admin panel at `/admin`. An admin user will log in approximately every 15 seconds.

The connection to the back-end is reset every 10 requests, so don't worry if you get it into a bad state - just send a few normal requests to get a fresh connection.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers HTTP request smuggling: "Response queue poisoning via H2.TE request smuggling".

## Solution steps

1. Using Burp Repeater, try smuggling an arbitrary prefix in the body of an HTTP/2 request using chunked encoding as follows. Remember to expand the Inspector's Request Attributes section and make sure the protocol is set to HTTP/2 before sending the request. `POST / HTTP/2 Host: YOUR-LAB-ID.web-security-academy.net Transfer-Encoding: chunked 0 SMUGGLED`
2. Observe that every second request you send receives a 404 response, confirming that you have caused the back-end to append the subsequent request to the smuggled prefix.
3. In Burp Repeater, create the following request, which smuggles a complete request to the back-end server. Note that the path in both requests points to a non-existent endpoint. This means that your request will always get a 404 response. Once you have poisoned the response queue, this will make it easier to recognize any other users' responses that you have successfully captured. `POST /x HTTP/2 Host: YOUR-LAB-ID.web-security-academy.net Transfer-Encoding: chunked 0 GET /x HTTP/1.1 Host: YOUR-LAB-ID.web-security-academy.net` Note Remember to terminate the smuggled request properly by including the sequence `\r\n\r\n` after the `Host` header.
4. Send the request to poison the response queue. You will receive the 404 response to your own request.
5. Wait for around 5 seconds, then send the request again to fetch an arbitrary response. Most of the time, you will receive your own 404 response. Any other response code indicates that you have successfully captured a response intended for the admin user. Repeat this process until you capture a 302 response containing the admin's new post-login session cookie. Note If you receive some 200 responses but can't capture a 302 response even after a lot of attempts, send 10 ordinary requests to reset the connection and try again.
6. Copy the session cookie and use it to send the following request: `GET /admin HTTP/2 Host: YOUR-LAB-ID.web-security-academy.net Cookie: session=STOLEN-SESSION-COOKIE`
7. Send the request repeatedly until you receive a 200 response containing the admin panel.
8. In the response, find the URL for deleting `carlos` (`/admin/delete?username=carlos`), then update the path in your request accordingly. Send the request to delete `carlos` and solve the lab.

## Vulnerability note

Underlying issue: HTTP request smuggling (CWE-444). Use a consistent, well-configured front-end/back-end HTTP stack; reject ambiguous Transfer-Encoding/Content-Length combinations.
