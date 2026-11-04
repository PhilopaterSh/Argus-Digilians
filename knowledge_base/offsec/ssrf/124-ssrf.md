# SSRF — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: ssrf
- cwe: CWE-918

## Scenario

Chain: enumerate, identify an internal-only secret route, then reach it via SSRF.

## Analysis / Response

Action (step 1):
```bash
gobuster dir -u http://127.0.0.1:5000 -w lab/wordlist.txt -q
```
