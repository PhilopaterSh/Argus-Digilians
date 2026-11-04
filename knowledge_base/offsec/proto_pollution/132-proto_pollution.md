# PROTO_POLLUTION — portswigger_labs_sft

- source: portswigger_labs_sft
- class: proto_pollution
- cwe: CWE-1321

## Scenario

I'm stuck on the PortSwigger lab "Client-side prototype pollution via browser APIs" (Practitioner, Prototype pollution). Here's the scenario:

This lab is vulnerable to DOM XSS via client-side prototype pollution. The website's developers have noticed a potential gadget and attempted to patch it. However, you can bypass the measures they've taken.

To solve the lab:

Find a source that you can use to add arbitrary properties to the global `Object.prototype`.

 Identify a gadget property that allows you to execute arbitrary JavaScript.

 Combine these to call `alert()`.

You can solve this lab manually in your browser, or use DOM Invader to help you.

This lab is based on real-world vulnerabilities discovered by PortSwigger Research. For more details, check out Widespread prototype pollution gadgets by Gareth Heyes.

Please give me the step-by-step solution.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Prototype pollution: "Client-side prototype pollution via browser APIs".

## Solution steps

1. In your browser, try polluting `Object.prototype` by injecting an arbitrary property via the query string: `/?__proto__[foo]=bar`
2. Open the browser DevTools panel and go to the Console tab.
3. Enter `Object.prototype`.
4. Study the properties of the returned object and observe that your injected `foo` property has been added. You've successfully found a prototype pollution source.

## Vulnerability note

Underlying issue: Prototype pollution (CWE-1321). Freeze prototypes where possible; avoid recursive merges of untrusted objects into Object.prototype.
