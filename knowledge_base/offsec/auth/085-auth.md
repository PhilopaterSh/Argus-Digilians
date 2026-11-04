# AUTH — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: auth
- cwe: CWE-287

## Scenario

Scenario: during a pentest I suspect API authentication weaknesses (JWT, API keys, OAuth tokens). How do I confirm and demonstrate it? Please emphasize weak API keys.

## Analysis / Response

## Overview
Burp Suite : The Summary tab of the token analysis report provided by Sequencer The token analysis report begins with a summary of the findings. The overall results include the quality of randomness within the token sample.

## Key points
In , you can see that the quality of randomness was extremely poor, indicating that we’ll likely be able to brute-force other existing tokens. To minimize the effort required to brute-force tokens, we’ll want to determine if there are parts of the token that do not change and other parts that often change. Importantly, use the character position analysis to determine feature under Character Set within the Character-Level Analysis tab. notably, the token character positions do not change all that much, with the exception of the final three characters; the string Ab4dt0k3n remains the same throughout the sampling.

## Approach
1. Typically, in , you can see that the quality of randomness was extremely poor, indicating that we’ll likely be able to brute-force other existing tokens.
2. To minimize the effort required to brute-force tokens, we’ll want to determine if there are parts of the token that do not change and other parts that often change.
3. Importantly, use the character position analysis to determine feature under Character Set within the Character-Level Analysis tab.
4. notably, the token character positions do not change all that much, with the exception of the final three characters; the string Ab4dt0k3n remains the same throughout the sampling.
5. When reviewing an application, now we know we should per form a brute force of only the final three characters and leave the remain der of the token untouched.

## Example
```
                  should then generate a report (see Figure 8-8).
                  which characters should be brute-forced (see Figure 8-9). You can find this
```

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.
