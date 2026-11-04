# INFO_DISCLOSURE — portswigger_labs_sft

- source: portswigger_labs_sft
- class: info_disclosure
- cwe: CWE-1385

## Scenario

How do I solve this PortSwigger Web Security Academy lab?

Title: Manipulating WebSocket messages to exploit vulnerabilities
Difficulty: Apprentice
Category: WebSockets

This online shop has a live chat feature implemented using WebSockets.

Chat messages that you submit are viewed by a support agent in real time.

To solve the lab, use a WebSocket message to trigger an `alert()` popup in the support agent's browser.

## Analysis / Response

This PortSwigger Web Security Academy lab (Apprentice) covers WebSockets: "Manipulating WebSocket messages to exploit vulnerabilities".

## Solution steps

1. Click "Live chat" and send a chat message.
2. In Burp Proxy, go to the WebSockets history tab, and observe that the chat message has been sent via a WebSocket message.
3. Using the browser, send a new message containing a `<` character.
4. In Burp Proxy, find the corresponding WebSocket message and observe that the `<` has been HTML-encoded by the client before sending.
5. Ensure that Burp Proxy is configured to intercept WebSocket messages, then send another chat message.
6. Edit the intercepted message to contain the following payload: `<img src=1 onerror='alert(1)'>`
7. Observe that an alert is triggered in the browser. This will also happen in the support agent's browser.

## Vulnerability note

Underlying issue: WebSockets (CWE-1385). Authenticate and authorize WebSocket messages the same as HTTP; validate origins and message schemas.
