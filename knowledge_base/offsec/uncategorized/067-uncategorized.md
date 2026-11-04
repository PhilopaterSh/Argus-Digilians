# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized
- cwe: CWE-919

## Scenario

How do I test for Android Application Security during an authorized bug bounty engagement, especially regarding android setup?

## Analysis / Response

## Overview
Use Android Studio emulator or a test device with developer options, adb, and a proxy (Burp) with the CA installed. Emulators simplify intercepting traffic.

## Deeper notes
Exported Activities/ContentProviders without permission checks, cleartext traffic, and secrets in resources/strings.xml are frequent wins. Bypass SSL pinning only on your test build/device to inspect API traffic.

## Focus: android setup
This section of the source material emphasizes **android setup**. When you practice, deliberately exercise that angle on a lab or in-scope target before moving on, and write down what signals confirmed or refuted the issue.

## Mitigation notes
Disable backup of sensitive data, avoid exported components without auth, certificate pinning done carefully, and no secrets in the APK.

## Verification & ethics
Confirm on your own test accounts whenever possible. Prefer non-destructive proofs (canary values, collaborator hits, harmless commands). Only test targets you are authorized to assess and stay inside program scope. If a step might affect other users or availability, pause and check the policy or ask the program. Manually verify automated findings before filing to protect your signal-to-noise reputation.

## Advanced tip
Look for filter bypasses, chain opportunities (e.g., redirect→OAuth, SSRF→metadata, XSS→CSRF), and less-tested surfaces like obscure content-types or secondary apps in scope.
