# PROTO_POLLUTION — h1

- source: h1
- class: proto_pollution
- cwe: CWE-400
- cve: ['CVE-2020-8136']
- severity: critical
- program: nodejs-ecosystem
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Prototype pollution in multipart parsing
**Affected Asset:** fastify

**Vulnerability Description:**
A critical-severity vulnerability was found that could allow an attacker to exploit a proto_pollution weakness. Specifically:

The application is affected by a critical-severity proto_pollution vulnerability. I would like to report a prototype pollution attack in fastify-multipart it allows to crash a remote server parsing multipart requests by sending a specially crafted request.

# Module

**module name:** fastify-multipart
**version:** all versions before < v1.0.5. v1.0.5 contains the fix. 
**npm page:** `https://www.npmjs.com/package/fastify-multipart`

## Module Description

[Fastify](https://www.fastify.io) plugin to parse the multipart content-type.

Under the hood it uses [busboy](http://npm.im/busboy).

## Module Stats

weekly downloads: 4900

# Vulnerability

## Vulnerability Description

Eran Hammer found this vulnerability for Hapi, he tested Fastify as well and found it vulnerable.
Here is the Hapi vulnerability report: https://www.npmjs.com/advisories/1479. 

## Steps To Reproduce:

> Detailed steps to reproduce with all required references/steps/commands. If there is any exploit code or reference to the package source code this is the place where it should be put.

## Patch

This was already released in https://github.com/fastify/fastify-multipart/pull/116 and version 1.0.5 issued.

# Wrap up

> Select Y or N for the following statements:

- I contacted the maintainer to let them know: Y
- I opened an issue in the related repository: N

I just need a CVE issued.

## Impact

It's a Denial of Service attack

The root weakness is Uncontrolled Resource Consumption.

**Steps to Reproduce:**
> Detailed steps to reproduce with all required references/steps/commands. If there is any exploit code or reference to the package source code this is the place where it should be put.

## Patch

This was already released in https://github.com/fastify/fastify-multipart/pull/116 and version 1.0.5 issued.

# Wrap up

> Select Y or N for the following statements:

- I contacted the maintainer to let them know: Y
- I opened an issue in the related repository: N

I just need a CVE issued.

## Analysis / Response

**Vulnerability Class:** proto_pollution
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** critical
**Endpoint Pattern:** https://www.npmjs.com/package/fastify-multipart

**Impact Assessment:**
It's a Denial of Service attack

**Remediation:**
Freeze Object.prototype. Use Map instead of plain objects for user-controlled keys. Validate and sanitize all object keys.
