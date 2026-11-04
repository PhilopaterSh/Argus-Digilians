# PROTO_POLLUTION — portswigger_labs_sft

- source: portswigger_labs_sft
- class: proto_pollution
- cwe: CWE-1321

## Scenario

Teach me the official solution for this PortSwigger Academy lab.

Lab: DOM XSS via client-side prototype pollution
Topic: Prototype pollution
Level: Practitioner

Scenario:
This lab is vulnerable to DOM XSS via client-side prototype pollution. To solve the lab:

Find a source that you can use to add arbitrary properties to the global `Object.prototype`.

 Identify a gadget property that allows you to execute arbitrary JavaScript.

 Combine these to call `alert()`.

You can solve this lab manually in your browser, or use DOM Invader to help you.

## Analysis / Response

This PortSwigger Web Security Academy lab (Practitioner) covers Prototype pollution: "DOM XSS via client-side prototype pollution".

## Solution steps

1. In your browser, try polluting `Object.prototype` by injecting an arbitrary property via the query string: `/?__proto__[foo]=bar`
2. Open the browser DevTools panel and go to the Console tab.
3. Enter `Object.prototype`.
4. Study the properties of the returned object. Observe that it now has a `foo` property with the value `bar`. You've successfully found a prototype pollution source.

## Vulnerability note

Underlying issue: Prototype pollution (CWE-1321). Freeze prototypes where possible; avoid recursive merges of untrusted objects into Object.prototype.
