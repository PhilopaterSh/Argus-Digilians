# Argus Security Framework — Spec-Kit Architecture Review

**Reviewer role:** Software/AI Engineering + Architecture (Spec-Driven Development)
**Review date:** 2026-07-05
**Scope reviewed:** `constitution.md`, `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`, and all 12 spec folders (`001`–`011`, including two colliding `003` features).
**Method:** Full read of every spec/plan/research/data-model; cross-spec consistency analysis; comparison against current SE + AI-engineering best practice. Where a fact is not present in the files, it is flagged as *Not specified* rather than assumed.

---

## 1. Executive Summary

Argus is a **local-first, autonomous AI penetration-testing framework** for Windows + WSL2/Kali, driven by a local Ollama LLM (`WhiteRabbitNeo-V3-7B`), a FAISS-backed RAG layer, a SQLite "Blackboard" memory, a tool-service registry that bridges into Kali, and a LangGraph agent loop, surfaced through a Streamlit GUI.

The **Spec-Kit discipline is genuinely strong** — a ratified constitution with non-negotiable principles, arc42/C4 architecture documentation, ADRs, and per-feature spec→plan→research→tasks decomposition. This is well above the median for a project of this size and is the single biggest asset here.

However, the **plan as a whole is not yet execution-ready**. It suffers from three classes of problem that are individually fixable but collectively block a clean build:

1. **Architectural drift across specs.** The RAG subsystem and the agent are each specified two-to-three different ways under different module names, with no "superseded-by" markers. `010` silently redesigns what `001`/`003-langgraph`/`004` already "implemented."
2. **A correctness bug in the core AI design** — the 3-tier embedding fallback (768-dim → 384-dim → 1536-dim) cannot work against a single fixed-dimension FAISS index. This is not a style issue; it will fail at runtime.
3. **Near-total absence of security guardrails** for an autonomous *offensive* tool: no authorization/scope/rules-of-engagement gate, despite the constitution restricting the tool to "authorized/CTF/educational" use. For an agent that autonomously exploits, this is the highest-severity gap.

**Overall planning-quality score: 6.5 / 10.** Excellent scaffolding and documentation; real, addressable technical and governance gaps in the substance.

**Recommendation:** Do **not** start implementing `010`/`011` as-is. Spend a short consolidation pass (est. 1–2 days) reconciling the specs, fixing the embedding-fallback design, and adding an authorization gate. Then proceed.

---

## 2. Understanding of the Project

From the files, my model of the system:

- **Purpose:** An "autonomous AI security reasoning engine" (arch doc §1) that lets an LLM plan and drive real Kali tooling (nmap, nuclei, crawlers, payload/evasion services) against targets, verify results reflectively to defeat WAF false-positives, self-heal missing dependencies, and persist all intelligence to a cross-session Blackboard.
- **Boundary model (constitution IV):** Windows host runs AI/GUI/orchestration; Kali-in-WSL runs the security tools; the only sanctioned crossing point is the WSL bridge / SSH:22.
- **Two cognitive subsystems (ADR-12):** LangChain for *linear deterministic RAG*; LangGraph for the *stateful cyclical pentest agent*. Every LLM call is enriched by **context fusion**: static knowledge (FAISS) + live target state (Blackboard), with an explicit "trust live over static" instruction (`001` data-model).
- **Install philosophy (constitution I–III):** one admin-elevating, idempotent, test-gated, single-file PowerShell installer (`002`).
- **Delivery model:** Spec-Kit workflow, English-only docs, commit-per-phase, dual-branch mirroring (`Argus` and `remote_Argus_PhilopaterSh`).

The intent is coherent and the ambition is appropriate. The gaps below are about *execution fidelity of the plan*, not about the vision.

---

## 3. Strengths (with reasons — kept because they are genuinely good)

- **Ratified constitution with NON-NEGOTIABLE principles.** Admin-first elevation, single-source installer, idempotent+test-gated, platform-boundary clarity, observability, English-only. These are the *right* invariants for this domain and they are enforced at a `/speckit.plan` gate. **Do not change this.**
- **Installer design (`002`) is excellent for its problem.** Self-elevate-once, embed dependencies as here-strings to guarantee zero external-file breakage, `-Offline`/`-DryRun`/`-Interactive` flags, per-step idempotency, timestamped logs, final summary table, archive-legacy-on-success. This is production-grade thinking. The Complexity-Tracking justification for embedding shell scripts is sound.
- **Explicit LangChain-vs-LangGraph separation (ADR-12).** Using a linear chain for RAG and a cyclic graph for the agent is the correct modern pattern; conflating them is a common mistake this project explicitly avoids.
- **Context-fusion with source separation and priority rule** (`===== STATIC KNOWLEDGE =====` / `===== LIVE TARGET STATE =====`, "trust live over static"). This is a strong, cheap anti-hallucination primitive and is well-specified in `001/data-model.md`.
- **`010` is a maturity leap in mindset.** Its principles — "never invent results in runtime," "keep demo/simulation isolated from production," "logs and state are first-class artifacts," "fail clearly, surface dependency status" — are exactly the right instincts for an agentic system. The truthful-state-reporting requirement (no synthetic open ports at runtime) is excellent.
- **SQLite Blackboard hardening (`003-sqlite-blackboard`)** correctly reaches for WAL mode, context-managed connections, a `schema_version` table, and a data-migration path. Right tool, right reliability concerns.
- **Reflective verification & rate-limit/IP-protection ADRs (6, 8).** Content-level validation instead of status-code trust, and halt-on-block logic, show real offensive-security domain awareness.

---

## 4. Weaknesses (gaps, drift, and incorrect assumptions)

**W1 — Duplicate spec numbering.** Two features share `003` (`003-langgraph-workflow`, `003-sqlite-blackboard`). Spec-Kit uses the numeric prefix as identity; this breaks tooling, ordering, and cross-references.

**W2 — RAG subsystem specified three incompatible ways under three module names.**
- `001` / `004` / arch-doc: `document_processor.py`, `vector_store.py`, `rag_engine.py`, with **structural** chunking.
- `010`: `processor.py`, `vectorstore.py`, `engine.py`, with plain `RecursiveCharacterTextSplitter` (linear).
These are different files *and* a different chunking philosophy. Nothing marks `010` as superseding `001`/`004`. A builder cannot tell which is canonical.

**W3 — The agent is specified two incompatible ways.**
- `003-langgraph-workflow` (marked **Implemented**): a *generic* dual-mode ReAct engine (prebuilt `create_react_agent` vs custom text-ReAct `StateGraph`) with a JSON/text dual parser.
- `010-langgraph-agent` (**Draft**): a *domain-specific* fixed node graph (Recon → Scanner → Exploit → Reflective → Post-Exploit).
These are fundamentally different agent architectures. There is no reconciliation note explaining whether `010` replaces `003` or wraps it.

**W4 — Ground-truth of "what exists" is unreliable.** `001/tasks.md` marks `brain_v2.py` as implemented; `005/spec.md` states `brain_v2.py` and `agent_factory_v2.py` "don't exist yet"; the arch doc references them as existing. Statuses (`Implemented` vs `Draft`) are not trustworthy across specs.

**W5 — Port configuration drift.** `003-langgraph` uses `8199`; `get_port.py` fails safe to `8501`; `011` expects `12199`. Three different "the" ports for the same dashboard — the exact class of bug the config-driven-port feature was meant to eliminate.

**W6 — No authorization / scope / rules-of-engagement control anywhere.** For an autonomous tool that scans and *exploits*, there is no spec for target allow-listing, scope boundaries, an explicit "I am authorized to test this" gate, or an audit trail of authorization. The constitution *asserts* authorized-use-only but nothing *enforces* it. (Expanded in §7 and §8.)

**W7 — No evaluation harness for the AI.** `004` adds unit tests for RAG modules, but there is no retrieval-quality eval (recall@k, MRR, faithfulness/groundedness), no agent task-success metric, and no golden dataset — despite "mitigate hallucinations" being a stated goal. You cannot regression-test reasoning quality.

**W8 — No CI/CD is specified.** Constitution mandates a syntax gate and dry-run gate, but these are described as *manual*. No GitHub Actions / pipeline spec exists, even though `006`/`009` say modules "pass import validation *in CI*" — referencing a CI that is never defined.

**W9 — Embedding fallback is dimensionally unsound** (correctness bug — see §5/§7).

**W10 — Assumption mismatches.** Python version is stated as `3.10+` (`001`, `003-langgraph`) and `3.12` elsewhere (`003-sqlite`, `004`, `005`, `006`, `010`). The tool count drifts (arch doc says "12 sub-services" in one table and lists 13; `003-sqlite` says "5+ modules"; `005` says "14 sub-services" and "42 public methods"). Minor individually, but they indicate the specs were not re-synced after edits.

---

## 5. Architecture Review

### What is good
- **Layering is clean and conventional:** GUI → Core (Brain/Agent) → RAG / Memory / Registry → Tools → WSL/Kali. This maps well to Clean-Architecture concentric layers and keeps the LLM out of direct OS calls.
- **The WSL bridge as a single crossing point** is a strong boundary (constitution IV) and is respected consistently in every plan's Constitution Check.
- **Blackboard-as-shared-state** is a legitimate multi-agent pattern (the classic "blackboard architecture") and is the right substrate for a cyclic agent.

### What needs change
- **Canonical module topology must be frozen.** Pick the `010` names (`processor/vectorstore/engine`, `agent/nodes/*`) *or* the `001` names — not both. Right now the arch doc (§5.1) and `010/plan.md` describe different trees. **Recommendation: adopt `010`'s tree as canonical** (it is the newest and cleanest) and rewrite the arch doc §5 to match, marking `001`/`003-langgraph`/`004` module layouts as historical.
- **Agent design must be unified.** The generic ReAct engine (`003`) and the fixed pentest node-graph (`010`) should not coexist unlabelled. **Recommendation:** make `010`'s explicit node graph the production agent, and either (a) retire `003`'s custom text-ReAct path, or (b) demote it to a single "reasoning" node *inside* `010`'s graph. A domain-specific bounded graph is safer and more observable than an open-ended ReAct loop for an offensive agent.
- **`brain.py` vs `brain_v2.py` vs `agent_factory` vs `agent_factory_v2`** is four overlapping controllers. Collapse to one Brain + one Agent-Factory. The `_v2` shadow-file pattern is technical debt that will rot.

### What can be improved (scalability/robustness)
- **FAISS flat index** is fine at the current scale (≤10K chunks). Document the crossover point (~1M vectors) where an ANN index (HNSW/IVF-PQ) becomes necessary, so it is a known future switch rather than a surprise.
- **Blackboard is single-writer SQLite.** Adequate for one agent process. If `010`'s multi-node graph ever runs nodes concurrently, define the write-serialization contract explicitly (WAL gives concurrent *readers*, not concurrent *writers*).

---

## 6. Spec-Kit Review (per feature)

| Feature | Verdict | Rationale |
|---|---|---|
| `001-rag-integration` | ⚠️ Needs update | Well-written and complete, but its module layout and structural-chunking design conflict with `010`. Mark as superseded/historical. |
| `002-consolidated-installer` | ✅ Appropriate | Best spec in the set. Only nit: FR-011 (byte-identical file across two branches) is brittle — prefer a single source of truth over hash-matching two copies. |
| `003-langgraph-workflow` | ❌ Not appropriate as-is | Renumber (collision) **and** reconcile with `010`. As a standalone generic ReAct engine it competes with the canonical agent. |
| `003-sqlite-blackboard` | ✅ Appropriate | Solid reliability spec. Renumber. Add: concurrent-writer contract, and an index plan for the 10K-findings SC. |
| `004-rag-pipeline` | ⚠️ Needs update | Correct instinct (harden + test), but it hardens the *`001` layout* that `010` abandons. Fold its test requirements into the canonical RAG. Its embedding-fallback verification must catch the dimensionality bug (§7). |
| `005-tool-registry` | ✅ Appropriate | Good plugin/`BaseToolService` abstraction (Open/Closed). Resolve the `brain_v2` existence contradiction; specify the 42-method backward-compat surface as an explicit contract, not prose. |
| `006-tactical-modules` | ✅ Appropriate | Clean structural refactor (import hygiene + strategy pattern). Low risk. Replace `print()` with the structured logger while you are in there (constitution V). |
| `007-reflective-verification` | ✅ Appropriate | Loop-detection via command history is the right idea; make the threshold configurable and back it with the Blackboard, as specified. |
| `008-self-healing` | ⚠️ Needs guardrails | `restart_service`/auto-`apt install` is an autonomous privileged action. Bound it: rate-limit, allow-list of services, and never auto-install arbitrary packages the LLM names. |
| `009-gui` | ⚠️ Redundant with `011` | Overlaps `011`. Decide: is Tkinter desktop still in scope, or does the unified Streamlit dashboard (`011`) replace it? Do not build both. |
| `010-langgraph-agent` | ⚠️ Canonical but unmarked | Should be declared the canonical agent+RAG spec, with `001/003/004` explicitly linked as superseded. Add the authorization gate (§7) and eval harness (§7) before implementing. |
| `011-gui-enhancement` | ⚠️ Depends on unfinished base | Strong product spec, but assumes `010` is "implemented and importable" (its own Assumptions) while `010`'s tasks are all unchecked. Sequence it strictly after `010`. Note: its Input is written in Arabic, violating constitution VI (English-only). |

---

## 7. AI Engineering Review

**Architecture (RAG + Agent).** The dual-brain split is correct. The two blocking issues:

- **Embedding fallback is dimensionally invalid (HIGH).** `001` FR-005..007 fall back Ollama `nomic-embed-text` (**768-dim**) → HF `all-MiniLM-L6-v2` (**384-dim**) → OpenAI `text-embedding-3-small` (**1536-dim**). A FAISS index is built at one fixed dimensionality. If the index was built with 768-dim vectors and Ollama is later down, querying with a 384-dim vector **raises a dimension-mismatch error**, not a graceful fallback. The fallback is only valid if the *entire index is rebuilt* with the fallback model — which contradicts the "graceful silent fallback at query time" story in `001`/`004`. **Fix:** pin one embedding model per index; record the model+dim in an index-manifest; on model change, force a full rebuild; treat "primary embedder unavailable AND index built with it" as *RAG-disabled* (fall through to Blackboard-only), which the non-blocking design already allows.

- **Retrieval quality is under-engineered (MEDIUM).** Single-vector dense retrieval, `k=4`, `chunk=600`, `similarity_threshold=0.5` (arbitrary), no re-ranking, no hybrid (BM25 + dense), no metadata filtering, no query expansion. For security cheatsheets where exact tokens matter (CVE IDs, flags, payload strings), **pure dense retrieval underperforms hybrid**. Add: (1) BM25 + dense hybrid with reciprocal-rank fusion, (2) a cross-encoder re-rank of the top-N, (3) metadata filters (source/type). These are the highest-ROI RAG upgrades and directly serve the anti-hallucination goal.

**Models / Prompting / Tool-calling.** `WhiteRabbitNeo-V3-7B` is non-tool-calling, which forces the brittle JSON/text dual-parser in `003`. Prefer **constrained decoding**: Ollama supports `format=json` (and JSON-schema-constrained output in recent versions) — use it to make Action emission reliable instead of regex-parsing free text. Keep the text-ReAct path only as a last-resort fallback. Also make the tool-calling-vs-not routing a first-class, tested capability probe (it already is in `003` FR-001 — good).

**Memory / Context management.** Blackboard is a good long-term store. *Not specified:* context-window budgeting. A fused prompt = top-k chunks + full Blackboard summary + graph triples + query can overflow a 7B model's context. Specify a token budget and a truncation/priority policy (live state first, then highest-similarity chunks).

**Agent guardrails (HIGH — safety-critical).** For an autonomous *exploitation* agent, the plan lacks:
- **Authorization/scope gate:** a required, logged "target ∈ authorized scope" check before any Recon/Scanner/Exploit node runs. Without it, an LLM misparse can point live offensive tooling at an out-of-scope host.
- **Action allow-listing:** the Exploit/Evasion/Simulation services should only run vetted commands; do not let the LLM assemble arbitrary shell strings for `CommandRunner` unconstrained.
- **Human-in-the-loop checkpoint** for high-impact nodes (Exploit, Post-Exploit) — LangGraph's `interrupt`/checkpointer supports this natively and fits `010`'s bounded-graph design.
- **OPSEC:** `SmartWebSearch` (DuckDuckGo) can leak target identifiers to a third party during an engagement — gate it behind an explicit opt-in.

**Evaluation (MEDIUM).** No eval harness (see W7). Add a small golden set for RAG (query→expected-chunk) scored on recall@k + faithfulness, and an agent scenario suite (e.g., the WAF-block→reflect→bypass loop asserted in `010` SC-002) run in CI. Without this, "reduces hallucination / improves accuracy" (ADR-10) is unfalsifiable.

**Observability (MEDIUM).** `010` Phase 3 (structured per-node events, durable run snapshots) is the right direction — make it the standard for *all* LLM/tool calls, not just the agent. Consider an OpenTelemetry/LangSmith-style trace per run (prompt, retrieved chunks, tool I/O, latency, tokens). This is also your primary debugging artifact.

**MCP.** *Not specified.* If external tool integrations grow, exposing tool services over **MCP** would decouple the registry from the process and align with current agent-tooling standards — worth a future ADR, not needed for MVP.

---

## 8. Software Engineering Review

- **Structure / layers:** Good separation (§5). Kill the `_v2` shadow files; one canonical module per concern.
- **Dependency management:** `Argus_venv` isolation is correct (constitution). *Risk:* dependencies are described in prose across specs (`requirements_embedded.txt`, langchain-*, faiss-cpu, sentence-transformers…) with no single pinned lockfile spec. Specify one pinned manifest with hashes; for a security tool, supply-chain pinning is not optional.
- **Testing strategy:** Unit coverage is planned per feature (good), but there is **no integration/e2e tier** against a real (or mocked-at-the-boundary) Ollama+WSL, and **no CI** (W8). Define a pyramid: unit (mocked) → integration (real Ollama, ephemeral SQLite) → a couple of e2e smoke runs. Wire the constitution's syntax + dry-run gates into CI.
- **CI/CD & deployment:** Absent. Add GitHub Actions: PowerShell `Parser::ParseFile` gate, `py_compile`, pytest, ruff/mypy, installer `-DryRun`. Deployment is "run the installer" — acceptable for this desktop tool, but document a versioned release artifact.
- **Security (beyond agent guardrails):**
  - Installer self-elevates and executes here-string shell content as root inside WSL — justified, but the embedded scripts must be integrity-checked (they are trusted-by-construction today; note it as an assumption).
  - Secrets via `.env` (arch §8) — good; add a spec-level rule that the Blackboard and logs must never persist credentials/tokens, and that report exports (`011`) are scrubbed.
  - `008` auto-remediation and `SelfHealingService` are privileged autonomous actions — bound them (rate-limit, allow-list) as noted.
- **Logging / monitoring:** Constitution V is strong, but multiple plans admit "logging needs work." Make a structured-logging module a shared dependency now (used by RAG, registry, modules, agent), rather than retrofitting per feature. Replace `print()` in `006` modules.
- **Error handling:** `010`'s "fail clearly, never fabricate" is the correct standard — promote it from a `010`-local principle to a **constitution amendment** so it binds every feature.
- **Configuration:** Centralize on `config.yaml` and eliminate the port drift (W5). One resolver, one default, all consumers read it.
- **Documentation:** arc42/C4 + ADRs are a real strength. Keep the arch doc in sync with the canonical module tree (it is currently ahead of/behind the specs in places).

---

## 9. Missing Opportunities

- **Authorization-as-a-first-class-node** in the LangGraph (entry gate) — turns the constitution's "authorized use only" from prose into enforced control.
- **Eval-driven development** for RAG and agent — a golden set + CI scoring would let you *prove* the anti-hallucination claims and prevent regressions.
- **Constrained JSON decoding** (`format=json`) — removes an entire brittle parser and class of bugs.
- **Hybrid retrieval + re-ranking** — the biggest single quality lever for a security knowledge base.
- **LangGraph checkpointer/persistence** — you already need durable run state (`010` Phase 3); using LangGraph's built-in checkpointer gives you pause/resume, human-in-the-loop, and time-travel debugging for free.
- **Single source of truth instead of dual-branch hash-mirroring** (`001` T018-19, `002` FR-011) — mirroring two directories and asserting equal hashes is fragile; a shared package or submodule removes the whole failure mode.
- **Report scrubbing + structured findings schema** (`011`) — you already have `SecurityReport` Pydantic; make it the canonical finding contract end-to-end (tool → Blackboard → report).

---

## 10. Recommended Changes (prioritized)

| Priority | Area | Current | Recommended | Why | Impact | Cost |
|---|---|---|---|---|---|---|
| P0 | AI correctness | 3-tier fallback across 768/384/1536-dim on one FAISS index | Pin one embedder per index + manifest + rebuild-on-change; disable RAG if primary+index mismatch | Current design throws dim-mismatch at runtime | Prevents core RAG failure | Low |
| P0 | Security/guardrails | No scope/authorization enforcement for an autonomous exploit agent | Mandatory authorization+scope gate node; action allow-list; HITL on Exploit/Post-Exploit | Prevents out-of-scope offensive actions; enforces constitution | Very high | Med |
| P0 | Spec integrity | RAG+agent specified 2–3 ways; duplicate `003`; unmarked supersession | Freeze canonical tree (adopt `010`); mark `001/003/004` superseded; renumber the `003` collision | Builders can't tell what's canonical | High | Low |
| P1 | AI quality | Dense-only, k=4, no re-rank, arbitrary threshold | Hybrid BM25+dense + cross-encoder re-rank + metadata filter | Directly improves grounding/accuracy | High | Med |
| P1 | Tool-calling | Regex JSON/text dual parser | Ollama `format=json` constrained decoding; text-ReAct as fallback only | Removes brittle parsing failure class | Med-high | Low |
| P1 | Eval | No retrieval/agent eval, no golden set | RAG recall@k + faithfulness; agent scenario suite; run in CI | Makes quality falsifiable + regression-safe | High | Med |
| P1 | CI/CD | Manual syntax/dry-run gates; "CI" referenced but undefined | GitHub Actions: PS parser, py_compile, pytest, ruff/mypy, installer -DryRun | Automates the constitution's own gates | High | Low-Med |
| P2 | Controllers | brain.py + brain_v2 + agent_factory + _v2 | Collapse to one Brain + one Agent-Factory | Removes shadow-file debt | Med | Med |
| P2 | Config | Ports 8199/8501/12199 diverge | One resolver, one default, all consumers read config.yaml | Eliminates the drift the feature was meant to fix | Med | Low |
| P2 | Autonomy safety | `008` auto apt/pip + restart unbounded | Rate-limit + service allow-list; never install LLM-named packages | Bounds privileged autonomous action | Med-high | Low |
| P2 | GUI scope | `009` (Tkinter) overlaps `011` (Streamlit) | Pick one; retire the other from scope | Avoids duplicate build | Med | Low |
| P3 | Context mgmt | No token budget for fused prompt | Define budget + truncation priority (live>static) | Prevents context overflow on 7B | Med | Low |
| P3 | Supply chain | Deps in prose, no single lock | One pinned, hashed manifest | Security-tool integrity | Med | Low |

---

## 11. Roadmap Improvements (suggested execution order)

The current numeric order does not reflect true dependencies. Proposed order:

1. **Consolidation sprint (new `012-spec-reconciliation`)** — freeze canonical module tree, resolve `003` collision, add "superseded-by" headers, sync arch doc, unify Python version, add the "never fabricate" principle to the constitution. *(Unblocks everything; ~1–2 days.)*
2. **`003-sqlite-blackboard`** — it is the substrate every other subsystem writes to; harden first.
3. **Canonical RAG (fold `001`+`004`+`010`-RAG)** — with the P0 embedding fix and P1 hybrid retrieval baked in from the start.
4. **`005-tool-registry`** — the abstraction the agent nodes depend on; resolve the `brain_v2` contradiction here.
5. **`007` + `008`** — reflective verification and *bounded* self-healing (guardrails included).
6. **Canonical agent (`010`)** — now that memory, RAG, and registry are stable; add the authorization gate + eval suite as acceptance criteria, not afterthoughts.
7. **`011` unified GUI** (retire `009` or keep Tkinter explicitly out of scope).
8. **`002` installer** — can proceed in parallel throughout; it is well-isolated.
9. **CI/CD** — stand up early (step 1–2), not last; it should be gating from the first consolidation PR.

---

## 12. Final Verdict

**Readiness:** The *planning framework* is ready and impressive; the *plan contents* are ~65% ready. It is not safe to begin implementing `010`/`011` until the P0 items are closed, because two of them (embedding-fallback correctness, unresolved canonical design) will cause rework, and one (authorization gate) is a safety obligation for an autonomous offensive tool.

**Principal risks:**
1. Building against the wrong/ambiguous RAG+agent design (drift) → rework.
2. RAG failing at runtime due to the dimensionality-fallback bug.
3. An autonomous exploit agent with no enforced scope/authorization.
4. Unfalsifiable quality claims (no eval) → silent regressions.
5. "CI-gated" requirements with no CI to gate them.

**Top 10 to do first:** (1) Fix embedding-fallback dimensionality. (2) Add mandatory authorization/scope gate + HITL on exploit nodes. (3) Freeze canonical module tree + resolve `003` collision + mark supersessions. (4) Stand up CI running the constitution's own gates. (5) Add hybrid retrieval + re-ranking. (6) Switch to `format=json` constrained decoding. (7) Add RAG + agent eval suites with a golden set. (8) Collapse `brain`/`brain_v2`/`agent_factory` duplication. (9) Bound `008` self-healing autonomy. (10) Unify port/config and pick one GUI.

**Safe to defer:** ANN index migration (HNSW/IVF), MCP externalization, Tkinter desktop (`009`) if Streamlit is chosen, advanced multi-agent orchestration (`010` explicitly scopes this out), and PDF/branded report polish (`011` P3).

**Do I recommend implementing now, or revising first?** **Revise first — but only a short, targeted pass.** Run the consolidation sprint (§11 step 1) plus the three P0 fixes. The scaffolding is strong enough that a 1–2 day reconciliation converts this from "impressive but ambiguous" into "execution-ready," after which the roadmap in §11 can proceed with confidence.

*Every recommendation above is tied to a concrete file/FR/ADR or an established engineering constraint; none is a change-for-change's-sake preference. Where the files did not contain information (CI details, token budgets, dependency locks, MCP), that absence is stated rather than assumed.*
