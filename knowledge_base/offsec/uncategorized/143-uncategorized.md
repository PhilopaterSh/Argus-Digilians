# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized
- cwe: CWE-283

## Scenario

What should a web pentester know about Enumerating Esoteric Attack Surfaces (Jann Moon): Date: Sun, 21 Jan 2024 02:59:02 GMT?

## Analysis / Response

Based on Enumerating Esoteric Attack Surfaces (Jann Moon) (Date: Sun, 21 Jan 2024 02:59:02 GMT):

Date: Sun, 21 Jan 2024 02:59:02 GMT

                      Content-Type: text/html

And checking this subdomain on nslookup points us to another story as
well.

                       nslookup signs.cat.com

Output:

     signs.cat.com       canonical name = redirect4.cat.com.

redirect4.cat.com           canonical                name                 =
86928b2876734aa5bb6e82d75a41b699.v1.radwarecloud.net.Name:
86928b2876734aa5bb6e82d75a41b699.v1.radwarecloud.net

Address: 66.22.73.126

So there is a lot of wonkiness inherent in how people implement these
things and the creative configurations they decide on can expose all
kinds of things that were meant to be internal. In the case of internal
servers, organizations typically have their local network configured to
handle the routing and as this content is not intended to be public,

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
