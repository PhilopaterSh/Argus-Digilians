# Data Model: Spec Consolidation & Architecture Reconciliation

**Phase**: 1 - Design | **Date**: 2026-07-05 | **Spec**: `specs/012-spec-reconciliation/spec.md`

---

## Purpose

This feature is primarily a governance/consolidation feature, so its "data model" is the set of
canonical structures the reconciliation defines or pins: the RAG embedding **manifest**, the
canonical **AgentState**, the canonical **module map**, and the **supersession registry**. Each is
the single authoritative shape that other features must conform to.

---

## Entity 1: EmbeddingManifest

Persisted at `app/core/rag/store/manifest.json`. One manifest per FAISS index. Introduced by
`spec.md` section 3 (FR-C1..C5); replaces the previous mtime-based auto-rebuild heuristic and the
separate checksum-file idea in `004`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `embedder_name` | str | yes | Model identifier, e.g. `nomic-embed-text` |
| `embedder_provider` | enum(`ollama`,`huggingface`,`openai`) | yes | Which backend produced the vectors |
| `dimension` | int | yes | Vector dimensionality (e.g. 768 for nomic, 384 for MiniLM, 1536 for OpenAI) |
| `knowledge_base_hash` | str (hex) | yes | Content hash of `knowledge_base/` at build time |
| `built_at` | str (ISO-8601) | yes | Build timestamp |
| `schema_version` | int | yes | Manifest schema version (starts at 1) |

**Invariants**:
- Exactly one embedder per index; `dimension` MUST match the FAISS index dimensionality.
- A load-time mismatch on `knowledge_base_hash` OR `embedder_name` triggers a full rebuild.
- If the pinned embedder is unavailable and no rebuild is possible, RAG is disabled (Blackboard-only);
  the index is never queried with a different-dimension vector.

**Example**:

```json
{
  "embedder_name": "nomic-embed-text",
  "embedder_provider": "ollama",
  "dimension": 768,
  "knowledge_base_hash": "a1b2c3d4e5f6",
  "built_at": "2026-07-05T00:00:00Z",
  "schema_version": 1
}
```

---

## Entity 2: AgentState (canonical)

The LangGraph `StateGraph` state for the canonical agent (`app/core/agent/state.py`). Consolidates
`010` (`current_target`, `payloads_tried`, `exploit_status`, `extracted_data`) with the durable
observability fields required by `spec.md` section 4 (FR-C6).

| Field | Type | Description |
|-------|------|-------------|
| `current_target` | str | Target under assessment |
| `messages` | list | Reasoning/message history (LangGraph channel) |
| `payloads_tried` | list[str] | Payloads attempted (Exploit/Reflective loop) |
| `exploit_status` | enum(`pending`,`blocked`,`success`,`failed`) | Current exploit outcome (truthful; never fabricated) |
| `extracted_data` | dict | Post-exploit extracted data |
| `retry_count` | int | Current retry count in the Exploit<->Reflective loop |
| `max_retries` | int | Configurable retry ceiling (bound for termination) |
| `final_state` | dict | Snapshot persisted to `logs/agent_runs/` on completion or failure |

**Invariants**:
- The graph MUST terminate on success, failure, or `retry_count == max_retries`.
- `exploit_status` MUST reflect real tool outcomes (Constitution VIII - Truthful Runtime).
- `final_state` is the durable record the UI reads (not in-memory session state).

---

## Entity 3: CanonicalModuleMap (reference)

The authoritative name for each concept (from `spec.md` section 2). Not persisted at runtime; it is
the reference table implementations and reviews check against.

| Concept | Canonical path / name | Deprecated alias (Replaced By canonical) |
|---------|-----------------------|------------------------------------------|
| RAG document processor | `app/core/rag/document_processor.py` (`DocumentProcessor`) | `processor.py` |
| RAG vector store | `app/core/rag/vector_store.py` (`VectorStore`) | `vectorstore.py` |
| RAG engine | `app/core/rag/rag_engine.py` (`RAGEngine`) | `engine.py` |
| Brain | `app/core/agent/brain.py` (`ArgusBrain`) | `app/core/brain.py`, `brain_v2.py` |
| Agent factory | `app/core/agent/agent_factory.py` | `agent_factory_v2.py` |
| Agent graph | `app/core/agent/graph.py` | `app/core/workflow/graph.py` |
| Memory | `app/core/memory/memory_service.py` (`ArgusMemory`) | - |
| Tool registry | `app/core/registry/tool_registry.py` (`ToolRegistry`) | - |
| Primary GUI | `app/GUI/dashboard.py` | `app/GUI/app.py`, `argus_gui.py` |

---

## Entity 4: SupersessionRegistry (reference)

The status of each feature spec after consolidation (from `plan.md` "Supersession Map"). Used by the
spec-validation CI stage (`spec.md` section 7) to assert no dangling supersession terms.

| Feature | Status | Marker |
|---------|--------|--------|
| `001-rag-integration` | Implemented | Refined By `012` section 3 |
| `004-rag-pipeline` | Draft | Refined By `012` section 3 |
| `009-gui` | Implemented | Primary UI Superseded By `011` |
| `010-langgraph-agent` | Draft (Canonical agent) | Names aligned to `012` section 2 |
| `013-langgraph-workflow` | Implemented | Partially Superseded By `010` + `012` |

---

## Relationships

```text
EmbeddingManifest 1---1 FAISS index (app/core/rag/store/)
AgentState        1---* node executions (Recon..Post-Exploit) --> final_state --> logs/agent_runs/
CanonicalModuleMap ---- governs ----> all feature specs + source modules
SupersessionRegistry -- validated by --> CI spec-validation stage
```

---

## Acceptance Criteria (data model)

- **AC-1**: A built index always has a `manifest.json` whose `dimension` equals the FAISS index
  dimensionality; no index is queried with a mismatched-dimension vector.
- **AC-2**: `AgentState` always terminates within `max_retries`; `final_state` is persisted for both
  completed and failed runs.
- **AC-3**: No source module or spec uses a name listed in the "Deprecated alias" column of
  CanonicalModuleMap except a forwarder explicitly marked deprecated.
- **AC-4**: Every entry in SupersessionRegistry has a resolving marker; CI fails if a `Superseded`/
  `Deprecated`/`Replaced By` term has no target.

---

## Implementation Notes

- The manifest is additive and non-breaking: it can be introduced (`tasks.md` T029) before the
  brain/agent consolidation lands.
- `AgentState` fields `retry_count`/`max_retries`/`final_state` are the minimum needed to satisfy the
  bounded-termination and observability requirements; nodes must not add fabricated fields.
