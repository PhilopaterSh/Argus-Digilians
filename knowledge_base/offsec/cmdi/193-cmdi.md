# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-74

## Scenario

What is the blast radius of malicious GraphQL input?

## Analysis / Response

One hostile argument can hit databases, sibling microservices, SSRF targets, and browsers of other users (stored XSS). Batching multiplies impact. Treat GraphQL like a multiplexed RCE/SQLi/SSRF surface, not “just JSON.” Black Hat GraphQL frames injection with OWASP Top 10 relevance.

**Delivery.** Prefer GraphQL variables so documents stay valid. Confirm sinks in resolvers (SQL/OS/HTML). Chain to XSS only in lab browsers with harmless payloads.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`injection`).
2. Prepare the lab or staging dependency the book assumes for `8 Injection` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `intermediate` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-74`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **8 Injection**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
