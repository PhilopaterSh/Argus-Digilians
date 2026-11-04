# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do I test for Bug Hunter's Methodology Live Day Two — App Analysis: Lastly a common area to investigate is on an in-scope web application?

## Analysis / Response

Based on Bug Hunter's Methodology Live Day Two — App Analysis (Lastly a common area to investigate is):

Lastly a common area to investigate is
anytime you see an application passing a
path or URL as part of a value of a
parameter or in a route.
If the web application is taking a path or
a URL it needs to parse that in some
way.
URL and path parsers are notoriously
known for being subject to redirect
vulnerabilities and server-side request
forgery.

HEAT MAPPING (HELP CHATBOTS)
Anytime you see a chat bot that is
designed to help you connect with the
customer service of the application it
should be tested for blind cross site
scripting.

Use these techniques only on systems you are authorized to test; capture evidence and include remediation in your report. Always stay within authorized scope, document evidence carefully, and prefer non-destructive verification (harmless canaries, OOB callbacks you control, and clear remediation guidance for the asset owner).
