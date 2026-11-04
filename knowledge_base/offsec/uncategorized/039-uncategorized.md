# UNCATEGORIZED — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: uncategorized

## Scenario

How do nmap Scripting Engine (NSE) invocations fit into a bash recon wrapper?

## Analysis / Response

Once ports are known, call useful default/safe scripts:

```bash
#!/bin/bash
HOST="${1}"
PORTS="${2:-22,80,443}"
nmap -sV -sC -p "${PORTS}" "${HOST}" -oN "nse_${HOST}.nmap"
# specific script examples
nmap -p 80 --script http-title,http-headers "${HOST}"
```

`-sC` enables the default script set. Parse `http-title` lines with grep for quick inventory. The book demonstrates nmap scripts during banner/OS phases — keep script scans targeted to avoid noisy, slow full-script blasts on large scopes.

**Context from the source.** Chapter 4 turns bash into a recon orchestrator: generate target lists, discover live hosts, port-scan with nmap/RustScan, parse greppable output, grab banners, fingerprint with Wappalyzer, and chain stages via files under loot/.

**Tooling habits.** Keep raw tool artifacts (`-oN`/`-oG`/`-oA`, Nikto `-output`, ffuf JSON) under an engagement `loot/` directory, parse copies rather than destructive edits, and sanity-check each binary with `--help`/`-h` after install or aliasing so PATH mistakes fail early.

**Scanning tip.** Prefer targeted ports from prior discovery over blind `-p-` on large sets; use `--open` to reduce noise; escalate to version/NSE only on confirmed listeners.

**Authorization.** All examples assume practice against the Black Hat Bash lab or other systems you are explicitly authorized to test.
