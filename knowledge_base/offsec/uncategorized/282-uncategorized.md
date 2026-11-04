# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How should I approach OWASP API Top 10 style issues during an authorized assessment, especially regarding common API failure patterns?

## Analysis / Response

## Overview
Broken User Authentication Broken user authentication refers to any weakness within the API authentica tion process. These vulnerabilities typically occur when an API provider either doesn’t implement an authentication protection mechanism or implements a mechanism incorrectly.

## Key points
56 Chapter 3 API authentication can be a complex system that includes several processes with a lot of room for failure. A couple decades ago, security expert Bruce Schneier said, “The future of digital systems is complexity, and complexity is the worst enemy of security.” As we know from the six constraints of REST APIs discussed in Chapter 2, RESTful APIs are supposed to be stateless. In order to be stateless, the provider shouldn’t need to remember the consumer from one request to another. For this constraint to work, APIs often require users to undergo a registration process in order to obtain a unique token.

## Approach
1. A useful way to think about this is that 56 Chapter 3 API authentication can be a complex system that includes several processes with a lot of room for failure.
2. A couple decades ago, security expert Bruce Schneier said, “The future of digital systems is complexity, and complexity is the worst enemy of security.” As we know from the six constraints of REST APIs discussed in Chapter 2, RESTful APIs are supposed to be stateless.
3. In order to be stateless, the provider shouldn’t need to remember the consumer from one request to another.
4. For this constraint to work, APIs often require users to undergo a registration process in order to obtain a unique token.
5. Users can then include the token within requests to demonstrate that they’re authorized to make such requests.

## Scope & safety
Confirm findings on your own test accounts whenever possible and prefer non-destructive proofs.
