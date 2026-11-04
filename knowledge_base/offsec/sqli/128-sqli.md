# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

Show me how Iterative NULL Method works in the context of SQL Injection, including the exact payloads/commands.

## Analysis / Response

**Iterative NULL Method** — this technique applies to SQL Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Systematically increase the number of columns in the `UNION SELECT` statement until the payload executes without errors or produces a visible change. Each iteration checks the compatibility of the column count.

```sql
UNION SELECT NULL;--
UNION SELECT NULL, NULL;-- 
UNION SELECT NULL, NULL, NULL;-- 
```
