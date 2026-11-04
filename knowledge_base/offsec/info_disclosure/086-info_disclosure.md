# INFO_DISCLOSURE — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: info_disclosure
- cwe: CWE-200

## Scenario

What's a minimal bash quick-and-dirty check for open /server-status on Apache?

## Analysis / Response

Chapter 5 motivates writing small custom scanners — example:

```bash
#!/usr/bin/env bash
while read -r base; do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "${base}/server-status")
  if [[ "${code}" == "200" ]]; then
    echo "[!] ${base}/server-status reachable (${code})"
  fi
done < urls.txt
```
Extend similarly for `/server-info`, `/.git/HEAD`, `/backup/`. Keep checks narrow, timeout-bound, and scoped — then graduate important ideas into Nuclei templates.

**Context from the source.** Chapter 5 (Early Access excerpt) applies bash to web assessment: Nikto batches, detecting/mirroring directory indexes, interpreting robots/CMS clues, and introducing ffuf/wfuzz/Nuclei-style scaling plus quick custom checks.

**Implementation habits.** Quote all expansions (`"${var}"`), validate inputs with `[[ -s file ]]` / `-z`/`-n` tests before launching tools, prefer `while read -r` for host files, and fail with an explicit non-zero `exit` when required arguments are missing so callers can branch cleanly.

**Scanning tip.** Prefer targeted ports from prior discovery over blind `-p-` on large sets; use `--open` to reduce noise; escalate to version/NSE only on confirmed listeners.

**Authorization.** All examples assume practice against the Black Hat Bash lab or other systems you are explicitly authorized to test.
