# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized
- cwe: CWE-350

## Scenario

During a bug bounty I want to try DNS Rebinding for DNS Rebinding. What are the payloads and when do they apply?

## Analysis / Response

**DNS Rebinding** — this technique applies to DNS Rebinding. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

> DNS rebinding changes the IP address of an attacker controlled machine name to the IP address of a target application, bypassing the [same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy) and thus allowing the browser to make arbitrary requests to the target application and read their responses.
