# CMDI — web_offensive_elite_v2_sft

- source: web_offensive_elite_v2_sft
- class: cmdi
- cwe: CWE-912

## Scenario

How does Black Hat Go structure a gRPC-based C2 RAT?

## Analysis / Response

Chapter 14 ties prior lessons into a RAT with three roles:

1. **Server** — persistent listener managing implant sessions.
2. **Client implant** — runs on the target, phones home.
3. **Admin component** — operator UI/CLI issuing tasks.

Communication uses **gRPC over HTTP/2** with a `.proto` schema defining RPCs (e.g. register, fetch tasks, push results). Generate Go stubs with `protoc` + `protoc-gen-go` / `protoc-gen-go-grpc`. Install `google.golang.org/grpc`.

Benefits: typed contracts, streaming options, and HTTP/2 framing that can blend with allowed egress. Lab only — unauthorized RATs are illegal.

**Teaching scope.** Keep implants allow-listed, kill-dated, and admin-bound to localhost. The gRPC schema should stay small until basics work. Pair every lab run with blue-team observations (process tree, egress destinations) so the exercise trains both sides.

### Practical walkthrough
1. Restate the goal in engagement language (authorized test only) and identify the systems in scope for this technique (`c2_rat`).
2. Prepare the lab or staging dependency the book assumes for `14 Building a Command-and-Control RAT` — disposable VMs/containers beat production every time.
3. Execute the minimal proof first (one target, one probe, one record) before scaling concurrency or wordlists.
4. Capture evidence suitable for a report: command/query, sanitized response, timestamps, tool version.
5. Map the issue to a control the customer can implement this sprint, not only a long-term architecture wish.

### Reporting & severity hints
- Difficulty labeled `advanced` in training metadata — calibrate language for that audience.
- CWE hint: `CWE-912`. Use it when it fits; leave blank in reports if no CWE cleanly applies.
- Always include reproduction preconditions (auth role, feature flag, network path).
- Offer both attacker impact and defender detection ideas so the fine-tuned model learns balanced answers.

### Source grounding
This guidance is synthesized from **Black Hat Go**, chapter **14 Building a Command-and-Control RAT**, without copying long passages. Prefer short snippets, verify APIs against current docs, and do not invent CVEs or lab IDs. If a library version drifted since publication, note that operators should check the module’s current README before shipping tooling.
