# ACCESS_CONTROL — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: access_control
- cwe: CWE-284

## Scenario

How would I build a continuous monitoring system to catch subdomain takeovers before others do?

## Analysis / Response

## Why monitor
Sites update DNS entries and remove third-party pages constantly, so new dangling CNAMEs appear unpredictably. Building automated monitoring lets you catch a takeover as soon as it becomes possible — before other hunters. The idea is simply to automate the manual process.

## Building blocks
1. **Compile and maintain a subdomain list.** Periodically scan the target for new subdomains; whenever you discover a new service, add it to your monitored list.
2. **Scan for CNAMEs pointing at vulnerable third-party services.** Resolve each subdomain's base DNS domain and decide whether it is hosted on a third party based on URL keywords (e.g., a URL containing `github.io` is GitHub Pages). Determine whether that provider is actually vulnerable to takeover; if the target's sites are only on non-vulnerable providers, you can skip them.
3. **Match unregistered-page signatures.** Most services return a custom 404 page for unclaimed names. For example, a GitHub Pages site is vulnerable if the response contains `There isn't a GitHub Pages site here`. Request each third-party-hosted subdomain and scan the response for these signature strings; a match flags a potential takeover.

## Running it
Make it run in the background and alert you only when it finds a suspected takeover. Schedule it with cron, e.g.:

    30 10 * * * cd /Users/vickie/scripts/security; ./subdomain_takeover.sh

When it notifies you, verify by registering the page on the external service. Keep the whole pipeline scoped to assets you are authorized to test.
