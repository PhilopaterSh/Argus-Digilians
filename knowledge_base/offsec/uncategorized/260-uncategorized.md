# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

Give me a checklist for testing Bug Bounty Program Selection.

## Analysis / Response

## Overview
Programs may list social apps, general web apps, Android/iOS mobile clients, REST/GraphQL APIs, open-source repositories, binaries, and hardware/IoT. Each demands different tooling and skill; beginners usually start with web apps and simple APIs.

## Deeper notes
Beginners thrive on wide-scope web programs with published writeups and reasonable first-time response times. Avoid programs with vague scope or histories of non-payment. Specialize (API, mobile, SSRF) once fundamentals are solid to reduce competition.

## Focus: asset types
This section of the source material emphasizes **asset types**. When you practice, deliberately exercise that angle on a lab or in-scope target before moving on, and write down what signals confirmed or refuted the issue.

## Testing checklist
1. List programs matching your skill level and asset preference.
2. Compare scope size, payout table, response stats, and competition.
3. Read out-of-scope carefully before testing.
4. Start with one primary and one secondary program to avoid context switching.

## Why these steps work
Following a consistent order reduces false negatives: you first understand the feature, then inject safely, then escalate only after a clear signal, and finally verify impact on a second principal. Skipping verification is how duplicates and Informative tickets happen.

## Verification & ethics
Confirm on your own test accounts whenever possible. Prefer non-destructive proofs (canary values, collaborator hits, harmless commands). Only test targets you are authorized to assess and stay inside program scope. If a step might affect other users or availability, pause and check the policy or ask the program. Manually verify automated findings before filing to protect your signal-to-noise reputation.

## Beginner tip
Master one lab for this topic end-to-end before hunting live. Write a short personal checklist you can reuse.
