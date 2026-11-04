# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-94
- cve: ['CVE-2020-8149']
- severity: high
- program: nodejs-ecosystem
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** [logkitty] RCE via insecure command formatting
**Affected Asset:** logkitty

**Vulnerability Description:**
I would like to report a `RCE` issue in the `logkitty` module.
It allows to execute `arbitrary commands remotely inside the victim's PC`

# Module
**module name:** `logkitty`
**version:** `0.7.0`
**npm page:** `https://www.npmjs.com/package/logkitty`

## Module Description
> Display pretty Android and iOS logs without Android Studio or Console.app, with intuitive Command Line Interface.

## Module Stats
[170,222] downloads in the last week

## Vulnerability Description
The issue occurs because a `user input` is formatted inside a `command` that will be executed without any check. The issue arises here: https://github.com/zamotany/logkitty/blob/master/src/android/adb.ts#L55

## Steps To Reproduce:
1. Check there aren't files called `HACKED` 
1. Execute the following commands in another terminal:

```bash
npm i logkitty # Install affected module
logkitty android app 'test; touch HACKED' #  Note the *touch command* is inside the *'* (single quote), so it's an argument, while it will be executed anyway
```
1. Recheck the files: now `HACKED` has been created :) {F754955}

## Patch
> Don't format `commands` using insecure `user's inputs` :)

## Supporting Material/References:
- [OPERATING SYSTEM VERSION]: Kali Linux
- [NODEJS VERSION]: 10.16.3
- [NPM VERSION]: 6.0.9

# Wrap up
- I contacted the maintainer to let them know: [N] 
- I opened an issue in the related repository: [N]

## Impact

`RCE` via command formatting on `logkitty`

**Steps to Reproduce:**
1. Check there aren't files called `HACKED` 
1. Execute the following commands in another terminal:

```bash
npm i logkitty # Install affected module
logkitty android app 'test; touch HACKED' #  Note the *touch command* is inside the *'* (single quote), so it's an argument, while it will be executed anyway
```
1. Recheck the files: now `HACKED` has been created :) {F754955}

## Patch
> Don't format `commands` using insecure `user's inputs` :)

## Supporting Material/References:
- [OPERATING SYSTEM VERSION]: Kali Linux
- [NODEJS VERSION]: 10.16.3
- [NPM VERSION]: 6.0.9

# Wrap up
- I contacted the maintainer to let them know: [N] 
- I opened an issue in the related repository: [N]

**Proof of Concept:**
```bash
npm i logkitty # Install affected module
logkitty android app 'test; touch HACKED' #  Note the *touch command* is inside the *'* (single quote), so it's an argument, while it will be executed anyway
```

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-94
**Weakness:** Code Injection
**Severity:** high
**Endpoint Pattern:** https://www.npmjs.com/package/logkitty

**Impact Assessment:**
`RCE` via command formatting on `logkitty`

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.
