# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What controls mitigate using Metasploit against web targets effectively (angle: post-exploitation web context) [Ch 7: Metasploit and Web]?

## Analysis / Response

## Overview
Inline The inline category of payloads contain their entire payload code inside them. This basically means that the exploit executes in one shot and is heavier in size.

## Key points
Although this variety of payload is very stable. Staged In staged payloads, when the exploit runs, it launches a little piece of code known as stager which re-establishes contact with the framework and then downloads the remaining piece of payload code, known as stage. In practice, so basically this is a two-staged process. Typically, iPv6 modules These modules work with the newer IPv6 networks.

## Additional notes
Meterpreter The Meterpreter is the de-facto payload in Metasploit. From a tester's perspective, it is a very advanced payload and it is executed in such a way that no file is ever written, basically by in-memory execution in the target. During authorized testing, once loaded, Meterpreter provides a plethora of post-exploitation modules, which you'll cover later in the Generating Web Backdoor Payload with Metasploit section. Reflective DLL injection This is specific to the Windows platform only.

## Remediation ideas
1. Prefer fixing the root cause: Meterpreter The Meterpreter is the de-facto payload in Metasploit.
2. Prefer fixing the root cause: From a tester's perspective, it is a very advanced payload and it is executed in such a way that no file is ever written, basically by in-memory execution in the target.
3. Prefer fixing the root cause: During authorized testing, once loaded, Meterpreter provides a plethora of post-exploitation modules, which you'll cover later in the Generating Web Backdoor Payload with Metasploit section.
4. Prefer fixing the root cause: In practice, reflective DLL injection This is specific to the Windows platform only.

## Scope & safety
Only test systems you are explicitly authorized to assess, and stay within the agreed scope.
