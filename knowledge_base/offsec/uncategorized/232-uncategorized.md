# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What is GraphQL and how do communications work at a high level?

## Analysis / Response

GraphQL is a query language and runtime for APIs. Clients send a **query document** describing the shape of data they need; the server validates it against a **schema** and executes **resolver** functions to populate each field.

Typical HTTP POST to `/graphql` with JSON body `{"query":"{ me { id name } }"}`. Responses are JSON with a `data` object and optional `errors` array. Unlike REST’s many endpoints, a GraphQL API usually exposes a single endpoint with a rich type system (objects, scalars, enums, unions, interfaces, inputs).

Black Hat GraphQL starts here so testers understand schemas, queries, and resolvers before attacking them.

**Tester takeaway.** Inventory operation types early and stop thinking in REST paths. Your mental model should be schema → operations → fields → arguments → resolvers. That map drives every later chapter’s techniques.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`graphql_basics`).
2. Prepare the lab or staging dependency the book assumes for `1 A Primer on GraphQL` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `beginner` in training metadata — calibrate language for that audience.
- CWE hint: `n/a`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **1 A Primer on GraphQL**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
