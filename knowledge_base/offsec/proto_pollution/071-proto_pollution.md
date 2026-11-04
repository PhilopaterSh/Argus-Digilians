# PROTO_POLLUTION — portswigger_labs_sft

- source: portswigger_labs_sft
- class: proto_pollution
- cwe: CWE-1321

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: Bypassing flawed input filters for server-side prototype pollution
Topic: Prototype pollution
Level: Practitioner

Scenario:
This lab is built on Node.js and the Express framework. It is vulnerable to server-side prototype pollution because it unsafely merges user-controllable input into a server-side JavaScript object.

To solve the lab:

Find a prototype pollution source that you can use to add arbitrary properties to the global `Object.prototype`.

 Identify a gadget property that you can use to escalate your privileges.

 Access the admin panel and delete the user `carlos`.

You can log in to your own account with the following credentials: `wiener:peter`

Note

 When testing for server-side prototype pollution, it's possible to break application functionality or even bring down the server completely. If this happens to your lab, you can manually restart the server using the button provided in the lab banner. Remember that you're unlikely to have this option when testing real websites, so you should always use caution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Prototype pollution: "Bypassing flawed input filters for server-side prototype pollution".

## Solution steps

1. Log in and visit your account page. Submit the form for updating your billing and delivery address.
2. In Burp, go to the Proxy > HTTP history tab and find the `POST /my-account/change-address` request.
3. Observe that when you submit the form, the data from the fields is sent to the server as JSON. Notice that the server responds with a JSON object that appears to represent your user. This has been updated to reflect your new address information.
4. Send the request to Burp Repeater.

## Vulnerability note

Underlying issue: Prototype pollution (CWE-1321). Freeze prototypes where possible; avoid recursive merges of untrusted objects into Object.prototype.
