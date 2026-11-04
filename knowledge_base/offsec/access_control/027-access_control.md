# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-863

## Scenario

Provide a GraphQL authn/authz testing checklist.

## Analysis / Response

- Detect auth layer presence
- Batching/CrackQL spray only with ROE
- JWT tampering lab checks
- Operation name allow-list bypass attempts
- Path enum to sensitive types
- Cross-account IDOR on queries & mutations
- Privilege escalation staff→admin fields

**Workflow.** Recon → config/DoS audit → authz → injection → forgery. Checklists prevent skipped classes when time-boxed. Keep a personal DVGA request library matched to each checkbox.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`checklist`).
2. Prepare the lab or staging dependency the book assumes for `Appendix A Testing Checklist` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `advanced` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-863`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat GraphQL**, chapter **Appendix A Testing Checklist**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
