# Feature Specification: Spec Consolidation & Architecture Reconciliation

**Feature ID**: `012-spec-reconciliation`

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-07-05

**Status**: Active — **Canonical / Authoritative**

**Authority**: This spec is the **single source of truth** for cross-cutting design decisions (module/package/class naming, RAG design, agent design, ports, parsing, testing, CI/CD). Where any other spec, plan, ADR, or the architecture document conflicts with this one, **this document wins** and the other document is to be updated to match. Feature-local behavior remains owned by each feature spec.

**Input**: Consolidate 12 previously-authored feature specs (`001`–`011`, plus the renumbered `013`) into one consistent, executable, maintainable plan. Remove architectural drift, unify terminology, eliminate duplication, and fix the concrete technical defects surfaced in the architecture review — **without** changing project goals or scope, and **without** introducing any usage-control / authorization / allow-list / human-in-the-loop / target-validation mechanism (explicitly out of scope for this effort).

---

## 1. Why this spec exists

The feature specs were written incrementally and never re-synchronized. This produced: duplicate numbering, the same subsystem described under different module names, two competing agent designs, one runtime-incorrect embedding-fallback design, three different ports for one service, and several stale "does-not-exist-yet" statements that later features resolved. This spec freezes the canonical answers so implementation can proceed against a single, coherent design.

---

## 2. Canonical Terminology & Naming (authoritative)

All specs, plans, ADRs, and code MUST use exactly these names.

### 2.1 RAG subsystem — canonical module layout

Location: `app/core/rag/`. **Canonical names win over `010`'s short names.** Reason: this layout is already implemented (`001`), hardened (`004`), and referenced by the architecture document and `005`; the descriptive names are clearer for maintenance and DX.

| Canonical module | Class | Superseded alias (do not use) |
|---|---|---|
| `app/core/rag/config.py` | `RAGConfig` | — |
| `app/core/rag/embeddings.py` | `EmbeddingFactory` | — |
| `app/core/rag/document_processor.py` | `DocumentProcessor` | `010`: `processor.py` |
| `app/core/rag/vector_store.py` | `VectorStore` | `010`: `vectorstore.py` |
| `app/core/rag/rag_engine.py` | `RAGEngine` | `010`: `engine.py` |
| `app/core/rag/store/` | (FAISS persistence dir) | — |
| `app/core/rag/store/manifest.json` | (embedder manifest — new, see §3) | — |

**Chunking:** structural chunking (Markdown-by-header, JSON-by-item/recursive, CSV-by-row, PDF-by-page) is canonical; `RecursiveCharacterTextSplitter` (chunk 600 / overlap 100) is the **fallback for plain/unknown formats only**. `010`'s "linear `RecursiveCharacterTextSplitter` for everything" is downgraded to this fallback path.

### 2.2 Agent subsystem — canonical module layout

Location: `app/core/agent/` (canonical for all brain/agent code, per Architecture v2 and `005`). **`app/core/workflow/` (from `013`) is superseded**; its reusable parts migrate here.

| Canonical module | Responsibility |
|---|---|
| `app/core/agent/brain.py` — `ArgusBrain` | Single reasoning interface: `_refresh_blackboard()` + `_enrich_with_rag()` context assembly, LLM invocation, structured-output handling, and registry-based tool dispatch (absorbs former `ArgusBrainV2.dispatch()`). |
| `app/core/agent/agent_factory.py` | Factory: `create_default_registry()`, `create_brain()`, `register_all_tools()` (absorbs `agent_factory_v2.py`). |
| `app/core/agent/state.py` — `AgentState` | LangGraph `StateGraph` state: `current_target`, `payloads_tried`, `exploit_status`, `extracted_data`, `messages`, `retry_count`, `max_retries`, `final_state`. |
| `app/core/agent/graph.py` | Canonical LangGraph builder (the explicit pentest node graph — see §4). Absorbs the capability probe, Action parser, and hooks migrated from `013`'s `app/core/workflow/`. |
| `app/core/agent/nodes/{recon,scanner,exploit,reflective,post_exploit}.py` | The five canonical agent nodes. |

**Deprecated shadow files (Replaced By the above):** `app/core/brain.py`, `app/core/brain_v2.py`, `app/core/agent/brain_v2.py`, `app/core/agent/agent_factory_v2.py`, and the whole `app/core/workflow/` package. These names MUST NOT appear in new specs; existing references are marked deprecated. Reason: eliminating `_v2` shadow files removes duplication and satisfies SRP/maintainability.

### 2.3 Memory subsystem — canonical

Location: `app/core/memory/memory_service.py` — `ArgusMemory`; canonical DB path `data/argus_intelligence.db` (single file, WAL mode). Owned by `003-sqlite-blackboard`. Unchanged; already consistent.

### 2.4 Tool subsystem — canonical

`app/core/registry/{base_tool.py (BaseToolService), tool_registry.py (ToolRegistry)}` (owned by `005`); `app/tools/tool_registry.py` (`WSLBridgeTools` facade, backward-compatible). Canonical registered-tool count: **17** (14 original + 3 reflective-verification tools added in `007`). All other counts in older docs ("12", "13", "14") are superseded by this number.

### 2.5 GUI subsystem — canonical

Primary UI: `app/GUI/dashboard.py` — the unified Streamlit "Argus Studio" dashboard (owned by `011`), launched by `scripts/LAUNCH_STUDIO.bat`. `app/GUI/desktop_gui.py` (Tkinter, from `009`) is retained as an **optional lightweight fallback**, not the primary UI. `app/GUI/app.py` and `app/GUI/argus_gui.py` are deprecated (aliased for backward compatibility per `011` FR-013).

### 2.6 Runtime constants — canonical

| Constant | Canonical value | Superseded values |
|---|---|---|
| Streamlit port (`streamlit.port` in `config.yaml`) | **12199** | `8199` (`013`), `8501` (get_port fallback) |
| `get_port.py` fail-safe default | **12199** (MUST equal configured default) | `8501` |
| Python / venv version | **3.12** | `3.10+` (`001`, `013`) |
| Primary embedding model | `nomic-embed-text` (Ollama, 768-dim) | — |
| Default LLM | `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` (overridable via `ARGUS_MODEL`) | — |

---

## 3. Canonical RAG Embedding Design (fixes the dimensionality defect)

**Problem being fixed:** `001` FR-005..007 specified a *query-time* fallback across embedders of different dimensionality (nomic 768 → MiniLM 384 → OpenAI 1536) against a single FAISS index. A FAISS index has a fixed dimension set at build time; querying it with a different-dimension vector raises a dimension-mismatch error, not a graceful fallback.

**Canonical rule — one embedder per index, recorded in a manifest, rebuilt on change:**

- **FR-C1**: Each FAISS index MUST be built with exactly **one** embedding model. The index directory MUST contain `store/manifest.json` recording: `embedder_name`, `embedder_provider` (ollama|huggingface|openai), `dimension`, `knowledge_base_hash` (content hash of `knowledge_base/`), `built_at`, and `schema_version`.
- **FR-C2**: The embedder fallback chain (Ollama → HuggingFace → OpenAI) applies **only at build time** — to select which embedder is available *when the index is (re)built*. The selected embedder is then pinned in the manifest.
- **FR-C3**: On `RAGEngine` load, the engine MUST compare the current configured/available embedder and `knowledge_base` hash against `manifest.json`. If either differs, it MUST trigger a **full rebuild** with the now-current embedder (and rewrite the manifest). This replaces the old "auto-rebuild on mtime" heuristic with a deterministic hash + embedder check.
- **FR-C4**: If the embedder that built the index is unavailable at query time and no rebuild is possible (e.g. offline, no fallback embedder present), RAG MUST degrade to **RAG-disabled** (Blackboard-only / raw-LLM path) rather than querying a dimension-mismatched index. This preserves the existing non-blocking guarantee (`001` FR-010) without the correctness bug.
- **FR-C5**: `manifest.json` doubles as the integrity/staleness artifact required by `004` FR-002 (supersedes the separate "checksum file" idea).

**Rationale:** guarantees vector/index dimensional consistency, makes rebuilds deterministic and observable, and keeps offline resilience — all without ever issuing an invalid query.

---

## 4. Canonical Agent Design (resolves the two competing designs)

**Decision:** the canonical production agent is the **explicit, bounded LangGraph node graph** from `010-langgraph-agent`:

```
Recon → Scanner → Exploit ⇄ Reflective → Post-Exploit → END
                     └────────(retry ≤ MAX_RETRIES)────────┘
```

- **Chosen because:** it is bounded (explicit `MAX_RETRIES` + recursion limit), observable (one structured event per node transition), domain-specific (maps to the real pentest lifecycle), and truthful (no synthetic results in runtime — `010`'s core principle). This is safer and more maintainable than an open-ended generic ReAct loop.
- **`013`'s generic dual-mode ReAct agent is superseded** as the top-level orchestrator. **Retained** from `013` and folded into `app/core/agent/`: (a) the model tool-calling capability probe, (b) the Action parser (now a *fallback* — see §5), (c) the pre/post model hooks, (d) config-driven port.
- **`ArgusBrain` is the reasoning callee**, not a competing orchestrator: nodes call `ArgusBrain` for LLM reasoning/RAG context and `ToolRegistry` for execution. There is exactly one Brain and one Agent-Factory (§2.2).

**Agent flow / memory / context management (canonical):**
- **FR-C6**: Every node transition MUST emit a structured event and persist a durable snapshot (`logs/agent_runs/`), and the UI MUST read that durable state (not only in-memory session state) — canonicalizing `010` Phase 3.
- **FR-C7**: The fused prompt MUST respect an explicit **context-token budget**: live Blackboard state first, then highest-similarity RAG chunks, truncating lowest-priority content when the budget is exceeded (prevents 7B context overflow). Priority rule "trust live over static" is retained from `001`.
- **FR-C8**: LangGraph persistence (checkpointer) SHOULD back durable run state to enable pause/resume and post-hoc inspection.

---

## 5. Canonical Tool-Output Parsing (Structured Output over Regex)

**Problem being fixed:** `013` parsed tool actions from free LLM text with a JSON-regex → text-regex chain — brittle.

- **FR-C9**: Action/tool selection MUST use **structured decoding** as the primary path: Ollama `format=json` (JSON-schema-constrained output) for the Action object `{ "tool": <name>, "input": <value> }`. For tool-calling-capable models, native `tool_calls` is used directly (via `create_react_agent`).
- **FR-C10**: The `013` regex dual-parser (JSON keys `name|action|tool` + `input|arguments|arg`, then text ReAct) is retained **only as a fallback** when structured decoding is unavailable or returns malformed output. Unrecognized output still returns a format-error for one retry.

**Rationale:** removes an entire class of parse failures, reduces retries/latency, and makes the contract explicit; the fallback preserves compatibility with models that cannot honor `format=json`.

---

## 6. Canonical Testing Strategy (applies to all features)

Every feature spec's test section MUST conform to this pyramid; features add cases, not new tiers.

- **Unit** (mocked boundaries): per-module, pytest. Owns: RAG modules, `ArgusMemory`, `ToolRegistry`, nodes, parser. Coverage target ≥ 90% for `memory_service.py`, ≥ 80% elsewhere.
- **Integration** (real Ollama + ephemeral SQLite + real FAISS): RAG build→query round-trip; Brain context assembly; registry dispatch; single-node execution against mocked tool I/O.
- **End-to-End (smoke)**: one full agent traversal (Recon→…→Post-Exploit) against a controlled local test target; one full RAG query; one GUI import+launch check.
- **AI Evaluation** (new — closes the "unfalsifiable quality" gap): a small golden set for RAG scored on **recall@k** and **faithfulness/groundedness**; an agent scenario suite asserting the bounded retry loop terminates on success or at `MAX_RETRIES` (`010` SC-002). Runs in CI as a non-blocking report first, then a gate.
- **Regression**: every fixed bug (starting with the embedding-dimension defect and the port drift) gets a locking test.
- **Performance**: RAG `similarity_search` < 500 ms @ 10K chunks (`001` SC-001, `004`); `get_blackboard_summary()` < 500 ms @ 10K findings (`003-sqlite` NFR-001); agent bounded by retry ceiling.

---

## 7. Canonical CI/CD Plan (fills the "CI referenced but undefined" gap)

A single pipeline (e.g. GitHub Actions) MUST provide these stages; this spec defines the plan, not the YAML.

1. **Lint** — `ruff` (Python), PSScriptAnalyzer (PowerShell).
2. **Type check** — `mypy` on `app/`.
3. **PowerShell syntax gate** — `[System.Management.Automation.Language.Parser]::ParseFile` zero-errors (constitution Development Workflow).
4. **Tests** — `pytest` unit + integration; publish coverage.
5. **AI-eval** — run the §6 evaluation suite; upload the report.
6. **Build validation** — installer `-DryRun` executes full control flow without mutation (constitution Dry-run gate); `py_compile` all edited modules.
7. **Spec validation** — check every `specs/*/` has spec+plan+tasks, no duplicate numeric prefixes, and no `Superseded`/`Deprecated` term left dangling without a target.
8. **Documentation validation** — English-only check (constitution VI) on committed docs; broken-internal-link check; architecture-doc naming-consistency check against §2.

These stages are exactly the constitution's existing manual gates (syntax, dry-run, English-only), now automated.

---

## 8. Requirements (this consolidation feature)

- **FR-001**: Resolve the duplicate `003` (done: `013-langgraph-workflow`).
- **FR-002**: Add `Superseded By` / `Deprecated` / `Replaced By` headers to every non-canonical spec (`001`, `004`, `013`) and stale reference (`005` Input, `009` vs `011`).
- **FR-003**: Publish the canonical naming table (§2) and ensure the architecture document and all specs use it.
- **FR-004**: Replace the query-time multi-dimension embedding fallback with the manifest design (§3) in `001`, `004`, `010`, and ADR-9.
- **FR-005**: Declare the canonical agent design (§4) and mark `013`'s generic agent superseded.
- **FR-006**: Consolidate `brain.py`/`brain_v2.py`/`agent_factory_v2.py` into a single Brain + Agent-Factory (§2.2).
- **FR-007**: Unify the port to `12199` across `013`, `get_port.py` fail-safe, `011`, and the architecture doc.
- **FR-008**: Mandate structured-output parsing (§5).
- **FR-009**: Adopt the canonical testing (§6) and CI/CD (§7) plans.
- **FR-010**: Standardize Python `3.12` everywhere.

---

## 9. Out of Scope (unchanged goals; explicit exclusions)

- No change to project goals, target platform, or the offensive/defensive feature set.
- **No usage-control mechanism of any kind** — no authorization enforcement, allow-lists, human-in-the-loop, or target validation. Absence of these is intentional and is **not** an open issue for this effort.
- No code implementation — this feature updates specs/plans/architecture/ADRs/tasks only.

---

## 10. Success Criteria

- **SC-001**: Zero duplicate spec numbers; every superseded spec carries a resolving header.
- **SC-002**: One name per module/class/service across all documents (§2); the architecture doc matches.
- **SC-003**: No document describes a query-time cross-dimension embedding fallback; all reference the manifest design.
- **SC-004**: Exactly one canonical agent design and one Brain referenced everywhere.
- **SC-005**: One port value (`12199`) in every document that mentions it.
- **SC-006**: Every feature's testing section conforms to the §6 pyramid; a CI/CD plan (§7) exists.
- **SC-007**: A reviewer can pick any subsystem and find a single, unambiguous canonical source.
