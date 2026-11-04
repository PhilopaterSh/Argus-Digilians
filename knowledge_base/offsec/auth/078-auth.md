# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-384

## Scenario

Walk me through Web Application Hacker's Handbook 2e — Time Dependency with practical steps and examples from the source material.

## Analysis / Response

Based on Web Application Hacker's Handbook 2e (Time Dependency):

Time Dependency
               Some web servers and applications employ algorithms to generate session tokens
               that use the time of generation as an input to the token’s value. If insufﬁcient
               other entropy is incorporated into the algorithm, you may be able to predict
               other users’ tokens. Although any given sequence of tokens on its own may
               appear to be random, the same sequence coupled with information about the
               time at which each token was generated may contain a discernible pattern. In a
               busy application with a large number of sessions being created each second, a
               scripted attack may succeed in identifying large numbers of other users’ tokens.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
