# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized
- cwe: CWE-1022

## Scenario

Help me understand Exploit as it relates to Tabnabbing, with the payloads from the field.

## Analysis / Response

**Exploit** — this technique applies to Tabnabbing. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

1. Attacker posts a link to a website under his control that contains the following JS code: `window.opener.location = "http://evil.com"`
2. He tricks the victim into visiting the link, which is opened in the browser in a new tab.
3. At the same time the JS code is executed and the background tab is redirected to the website evil.com, which is most likely a phishing website.
4. If the victim opens the background tab again and doesn't look at the address bar, it may happen that he thinks he is logged out, because a login page appears, for example.
5. The victim tries to log on again and the attacker receives the credentials
