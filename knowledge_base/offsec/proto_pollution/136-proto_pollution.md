# PROTO_POLLUTION — portswigger_labs_sft

- source: portswigger_labs_sft
- class: proto_pollution
- cwe: CWE-1321

## Scenario

I'm stuck on the PortSwigger lab "Detecting server-side prototype pollution without polluted property reflection" (Practitioner, Prototype pollution). Here's the scenario:

This lab is built on Node.js and the Express framework. It is vulnerable to server-side prototype pollution because it unsafely merges user-controllable input into a server-side JavaScript object.

To solve the lab, confirm the vulnerability by polluting `Object.prototype` in a way that triggers a noticeable but non-destructive change in the server's behavior. As this lab is designed to help you practice non-destructive detection techniques, you don't need to progress to exploitation.

You can log in to your own account with the following credentials: `wiener:peter`

Note

 When testing for server-side prototype pollution, it's possible to break application functionality or even bring down the server completely. If this happens to your lab, you can manually restart the server using the button provided in the lab banner. Remember that you're unlikely to have this option when testing real websites, so you should always use caution.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Prototype pollution: "Detecting server-side prototype pollution without polluted property reflection".

## Solution steps

1. Log in and visit your account page. Submit the form for updating your billing and delivery address.
2. In Burp, go to the Proxy > HTTP history tab and find the `POST /my-account/change-address` request.
3. Observe that when you submit the form, the data from the fields is sent to the server as JSON. Notice that the server responds with a JSON object that appears to represent your user. This has been updated to reflect your new address information.
4. Send the request to Burp Repeater.
5. In Repeater, add a new property to the JSON with the name `__proto__`, containing an object with an arbitrary property: `"__proto__": { "foo":"bar" }`
6. Send the request. Observe that the object in the response does not reflect the injected property. However, this doesn't necessarily mean that the application isn't vulnerable to prototype pollution.

## Vulnerability note

Underlying issue: Prototype pollution (CWE-1321). Freeze prototypes where possible; avoid recursive merges of untrusted objects into Object.prototype.
