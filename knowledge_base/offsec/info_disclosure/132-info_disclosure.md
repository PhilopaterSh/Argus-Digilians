# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

How do I find subscription operations for CSWSH testing?

## Analysis / Response

Introspect for `subscription` root fields; search client JS for `subscription` keywords; watch WS traffic in Burp while using the app. Note auth mechanism on the upgrade request. Only proceed with hijack PoCs in authorized lab conditions.

**Scope.** Cookie-authenticated WebSocket subscriptions are the risk. Validate Origin and prefer explicit tokens. Distinguish subscription authz bugs from true CSWSH in write-ups.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`cswsh`).
2. Prepare the lab or staging dependency the book assumes for `9 Request Forgery and Hijacking` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `advanced` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-200`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **9 Request Forgery and Hijacking**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
