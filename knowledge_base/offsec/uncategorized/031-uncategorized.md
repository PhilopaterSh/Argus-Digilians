# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What mitigations are effective against API Security Testing?

## Analysis / Response

## Overview
Classic web bugs apply: IDOR on /users/{id}, mass assignment, broken function-level auth, injection in JSON fields, rate-limit gaps, and JWT alg/none or key confusion.

## Deeper notes
APIs often expose more object IDs and admin methods than HTML UIs. Test verb tampering (GET vs DELETE), batch endpoints, and GraphQL authorization per field. Document exact paths and auth headers in the report.

## Focus: api bugs
This section of the source material emphasizes **api bugs**. When you practice, deliberately exercise that angle on a lab or in-scope target before moving on, and write down what signals confirmed or refuted the issue.

## Defensive guidance
Per-object authorization, schema validation, rate limiting, and short-lived scoped tokens.
Add regression tests so the fix cannot silently disappear in a refactor. Security code reviews should treat this class as a checklist item for new features.

## Verification & ethics
Confirm on your own test accounts whenever possible. Prefer non-destructive proofs (canary values, collaborator hits, harmless commands). Only test targets you are authorized to assess and stay inside program scope. If a step might affect other users or availability, pause and check the policy or ask the program. Manually verify automated findings before filing to protect your signal-to-noise reputation.

## Advanced tip
Look for filter bypasses, chain opportunities (e.g., redirect→OAuth, SSRF→metadata, XSS→CSRF), and less-tested surfaces like obscure content-types or secondary apps in scope.
