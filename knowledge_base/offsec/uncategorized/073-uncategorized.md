# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What distinguishes GraphQL Cop from CrackQL?

## Analysis / Response

Cop audits configuration/DoS posture; CrackQL attacks credentials/arguments with wordlists. Use Cop early for hygiene findings; CrackQL later with strict ROE. Both are in the book’s tooling kit.

**Deliverable.** Endpoint list, engine fingerprint, introspection status (HTTP+WS), IDE exposure, auth mechanism, GET support. This recon sheet feeds DoS/authz/injection planning and belongs in the appendix of the report.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`recon_tooling`).
2. Prepare the lab or staging dependency the book assumes for `2 Setting Up a GraphQL Security Lab` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `beginner` in training metadata — calibrate language for that audience.
- CWE hint: `n/a`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **2 Setting Up a GraphQL Security Lab**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
