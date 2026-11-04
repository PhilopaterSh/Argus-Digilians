# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-639

## Scenario

What is BOLA and how do I start testing an API for it?

## Analysis / Response

Broken Object Level Authorization (BOLA) remains one of the most prominent API vulnerabilities and is often one of the easiest to test for. It occurs when an API provides an authenticated user access to resources they shouldn't be authorized to see. Crucially, predictable resource IDs don't themselves make an API vulnerable - the flaw exists only when the provider fails to check that the requester is authorized for the requested resource. Insecure APIs commonly verify that a user is authenticated but not that they're authorized.

To start testing: if the API exposes resources in a pattern, test other instances of that pattern. For example, if a receipt loads at /api/v1/receipt/135, use 135 as a payload position in Burp Intruder or Wfuzz and iterate 0-200.

Keep these in mind:
- BOLA isn't only in GET requests - try all methods against resources you shouldn't access.
- Vulnerable IDs aren't only in the URL path - check the request body and headers too.
- Look beyond simple integers: user/resource/organization IDs (names or numbers), emails, phone numbers, addresses, tokens, and encoded payloads are all used to retrieve resources.

The cleanest confirmation is A-B testing: create a resource as UserA, then request it with UserB's token. A successful response for another user's private data (name, email, SSN, bank details) confirms BOLA.
