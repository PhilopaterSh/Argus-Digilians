# Reference Material From Orphan Branches

This folder preserves non-core material ported from Git branches whose
history is unrelated to `main` (they were created as independent repository
uploads, so a normal git merge is impossible - content was ported manually).

## momen/

Source branch: `argus/momen` (last activity 2026-07-12).

| Item | Why it is kept | Why it is NOT merged as code |
|------|----------------|------------------------------|
| `AI_NATIVE_MIGRATION_AUDIT.md` | High-quality architectural audit of the older flat architecture with an AI-native migration roadmap. Several of its recommendations were later implemented independently in `main` (real RAG under `app/core/rag/`, LangGraph workflow under `app/core/agent/`). | Documentation only. |
| `_experimental_advanced_modules/` | Experimental standalone modules (payload decider, LLM engine, payload encoder, verifier). Reference for future feature work. | Never integrated upstream, no tests, imports assume the old flat `core/` layout. |

`momen`'s runnable code (`core/*.py`, old `GUI/app.py`, `reports/report_engine.py`)
was **not** ported: `main`'s Clean Architecture implementation supersedes it
(see the audit doc's own finding that the old "RAG" was static dicts).
His 1000-scenario knowledge base lives on as a *data* asset at
`knowledge_base/agent_playbook_scenarios.json` and is ingested into the real
RAG pipeline by `scripts/ingest_scenarios_kb.py`.

## moustafa-side-project/

Source branch: `argus/MOUSTAFA-PC`, single commit `8e16cd4` (2026-06-09).

A small standalone multi-agent search experiment (`ai_agents_aroject/` in the
original commit: search agents with JSON memory). Unrelated to the Argus
pentesting pipeline; kept for reference only.
