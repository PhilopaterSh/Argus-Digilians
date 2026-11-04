# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

What controls mitigate API security test preparation and lab setup effectively (angle: scoping API engagements) [Ch 0: Preparing for API Security Testing]?

## Analysis / Response

## Overview
Rate Limit Testing Rate limiting is a restriction on the number of requests an API consumer can make within a given time frame. It is enforced by an API provider’s web servers, firewall, or web application firewall and serves two important pur poses for API providers: it allows for the monetization of APIs and prevents the overconsumption of the provider’s resources.

## Key points
Because rate limiting is an essential factor that allows organizations to monetize their APIs, you should include it in your scope during API engagements. For example, a business might allow a free-tier API user to make one request per hour. Typically, once that request is made, the consumer would be kept business a fee, they could make hundreds of requests per hour. Without adequate controls in place, these non-paying API consumers could find ways to skip the toll and consume as much data as often as they please. testing consists of attacks that are intended to disrupt services and make the systems and applications unavailable to users.

## Additional notes
Importantly, whereas DoS testing is meant to assess how resilient an organization’s computing resources are, rate limit testing seeks to bypass restrictions that limit the quantity of requests sent within a given time frame. Attempting to bypass rate limiting will not necessarily cause a disruption to services. Importantly, instead, bypassing rate limiting could aid in other attacks and demonstrate a weakness in an organization’s method of monetizing its API. Typically, an organization publishes its API’s request limits in the API documentation.

## Remediation ideas
1. Prefer fixing the root cause: Importantly, whereas DoS testing is meant to assess how resilient an organization’s computing resources are, rate limit testing seeks to bypass restrictions that limit the quantity of requests sent within a given time frame.
2. Prefer fixing the root cause: Typically, attempting to bypass rate limiting will not necessarily cause a disruption to services.
3. Prefer fixing the root cause: Importantly, instead, bypassing rate limiting could aid in other attacks and demonstrate a weakness in an organization’s method of monetizing its API.
4. Prefer fixing the root cause: Typically, an organization publishes its API’s request limits in the API documentation.

## Scope & safety
If a step could affect availability or other users, pause and check the engagement rules first.
