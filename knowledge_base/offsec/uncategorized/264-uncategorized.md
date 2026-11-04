# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I test for Enumerating Esoteric Attack Surfaces (Jann Moon): Spidering For Endpoints on an in-scope web application?

## Analysis / Response

Based on Enumerating Esoteric Attack Surfaces (Jann Moon) (Spidering For Endpoints):

Spidering For Endpoints

Part two of the endpoint expansion saga will discuss the well-known art
of spidering. Spidering works in much of the way that search engine
bots index the internet; you feed it a page and the spider extracts all the
links from it. Then each of those links is visited and the subsequent
page is scanned for links. You repeat this until you discover the entire
internet or run out of new places to look. This is generally done
automatically, though doing some of it manually can give you a much
better understanding of the functionality and organization of the web
app you are testing.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
