# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-307

## Scenario

How do I use CrackQL during GraphQL auth testing?

## Analysis / Response

CrackQL is built for GraphQL password spraying/stuffing and argument brute force. Provide endpoint, mutation/query template with placeholders, and candidate lists. Start with very small lists on lab/DVGA; coordinate lockout with the customer on real tests. Log successes securely.

**Throttle ethics.** Batching/CrackQL sprays are lockout-prone. Use DVGA for muscle memory; on real programs get explicit ROE, tiny lists, and monitoring. JWT tests stay on staging tokens you control.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`auth_bypass`).
2. Prepare the lab or staging dependency the book assumes for `7 Authentication and Authorization Bypasses` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `advanced` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-307`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **7 Authentication and Authorization Bypasses**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
