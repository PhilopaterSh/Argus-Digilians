# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

How does Clairvoyance automate schema reconstruction?

## Analysis / Response

Clairvoyance uses wordlists + suggestion/error oracles to iteratively discover types and fields when introspection is off. Feed it the endpoint and a wordlist; review the recovered schema critically (false positives happen). Combine with manual Burp replay for confirmation.

**Assume leakage.** If introspection is off, still try suggestions, `__type`, staging, and JS bundles. Verbose errors alone can rebuild much of the schema. Recommend sanitizing client errors and disabling IDEs in prod.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`information_disclosure`).
2. Prepare the lab or staging dependency the book assumes for `6 Information Disclosure` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `advanced` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-200`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **6 Information Disclosure**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
