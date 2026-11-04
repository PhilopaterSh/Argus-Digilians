# RESOURCE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: resource
- cwe: CWE-400

## Scenario

What is array-based query batching and why is it dangerous?

## Analysis / Response

Some servers accept a JSON **array** of query objects in one POST, executing many operations under one HTTP request / one auth context:
```json
[{"query":"..."},{"query":"..."}]
```
Abuse: amplify DoS; bypass per-request rate limits; pack many login attempts. Detect with **BatchQL**. Defend by disabling batching or capping array length; apply rate limits per operation.

**Permission gate.** Application-layer GraphQL DoS can flatten shared staging. Start tiny, watch metrics with the owner, and stop at proof. Report missing depth/cost/batching limits even when you did not fully exhaust CPU.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`graphql_dos`).
2. Prepare the lab or staging dependency the book assumes for `5 Denial of Service` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `advanced` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-400`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **5 Denial of Service**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
