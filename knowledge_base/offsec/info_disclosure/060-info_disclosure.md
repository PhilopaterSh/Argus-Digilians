# INFO_DISCLOSURE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: info_disclosure
- cwe: CWE-1385

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Manipulating the WebSocket handshake to exploit vulnerabilities
Topic: WebSockets
Level: Practitioner

Scenario:
This online shop has a live chat feature implemented using WebSockets.

It has an aggressive but flawed XSS filter.

To solve the lab, use a WebSocket message to trigger an `alert()` popup in the support agent's browser.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers WebSockets: "Manipulating the WebSocket handshake to exploit vulnerabilities".

## Solution steps

1. Click "Live chat" and send a chat message.
2. In Burp Proxy, go to the WebSockets history tab, and observe that the chat message has been sent via a WebSocket message.
3. Right-click on the message and select "Send to Repeater".
4. Edit and resend the message containing a basic XSS payload, such as: `<img src=1 onerror='alert(1)'>`
5. Observe that the attack has been blocked, and that your WebSocket connection has been terminated.
6. Click "Reconnect", and observe that the connection attempt fails because your IP address has been banned.
7. Add the following header to the handshake request to spoof your IP address: `X-Forwarded-For: 1.1.1.1`
8. Click "Connect" to successfully reconnect the WebSocket.
9. Send a WebSocket message containing an obfuscated XSS payload, such as: `<img src=1 oNeRrOr=alert`1`>`

## Vulnerability note

Underlying issue: WebSockets (CWE-1385). Authenticate and authorize WebSocket messages the same as HTTP; validate origins and message schemas.
