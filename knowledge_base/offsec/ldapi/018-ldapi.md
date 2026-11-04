# LDAPI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ldapi
- cwe: CWE-90

## Scenario

I need to craft LDAP Injection payloads via Defaults Attributes. What should I know and what do I send?

## Analysis / Response

**Defaults Attributes** — this technique applies to LDAP Injection. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

Can be used in an injection like `*)(ATTRIBUTE_HERE=*`

```bash
userPassword
surname
name
cn
sn
objectClass
mail
givenName
commonName
```
