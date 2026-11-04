# RESOURCE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: resource
- cwe: CWE-400

## Scenario

What real-world GraphQL DoS cases does Black Hat GraphQL highlight?

## Analysis / Response

Case studies include large payloads (HackerOne), ReDoS via regular expressions (CS Money), circular introspection (GitLab), alias field duplication (Magento), array batching duplication (WPGraphQL), and circular fragments (Agoo). Use them as patterns: when you see aliases/batching/introspection open, check the matching class.

**Use responsibly.** Public cases calibrate severity and suggest test ideas; always reproduce on the target with your evidence. Do not paste third-party exploit code into production assessments.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`case_studies`).
2. Prepare the lab or staging dependency the book assumes for `10 Disclosed Vulnerabilities and Exploits` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `intermediate` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-400`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **10 Disclosed Vulnerabilities and Exploits**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
