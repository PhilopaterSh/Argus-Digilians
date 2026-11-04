# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What Mongo injection vs legitimate miner querying distinction should the model learn?

## Analysis / Response

Miner uses valid authenticated API queries. Injection attacks craft hostile filters against exposed endpoints. Label training data accordingly (`database_mining` tooling vs web injection). Black Hat Go ch7 is miner/post-ex, not SQLi payloads.

**Minimize harm.** Prefer read-only DB users, `LIMIT` samples, and counts before dumps. Automate interesting-column heuristics but require operator confirmation before exporting PII. Dockerized labs are the right place to practice destructive mistakes.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`database_mining`).
2. Prepare the lab or staging dependency the book assumes for `7 Abusing Databases and Filesystems` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `beginner` in training metadata — calibrate language for that audience.
- CWE hint: `n/a`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat Go**, chapter **7 Abusing Databases and Filesystems**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
