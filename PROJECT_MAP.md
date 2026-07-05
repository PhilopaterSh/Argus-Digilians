# Argus Security Framework — Project Map (what runs what)

This folder is a **cleaned, filtered copy** of the Argus project. Everything here is
a file that actually powers the running application. Duplicate/old versions, scan
artifacts, caches, and generated reports were left out to remove the "folder inside
folder, who-runs-who" confusion.

> **Source of truth:** this clean build was assembled from
> `FINAL_STABLE_SECURITY_PROJECT/`, which is the version every launcher/installer in
> the original repo actually pointed to (see "Why this version" below).

---

## 1. Quick Arabic guide — دليل سريع

- **ده المشروع الحقيقي اللي بيشتغل**، متجمّع في مكان واحد ومترتب.
- عايز تشغّل الواجهة (الموقع): دوس على `LAUNCH_STUDIO.bat`.
- عايز تشغّل من التيرمنال: `LAUNCH_CLI.bat`.
- الكود الأساسي كله جوه فولدر `core/`.
- الملفات المتقدمة الزيادة من نسخة GradProject متحطّة في `_experimental_advanced_modules/` — **اختيارية** ومش مطلوبة للتشغيل.
- شرح كل ملف بيعمل إيه تحت في القسم رقم 3.

---

## 2. The execution flow (start → finish)

```
                        ┌──────────────────────────────┐
   USER  ──────────────▶│  ENTRY POINT                 │
                        │  • LAUNCH_STUDIO.bat → GUI    │
                        │  • LAUNCH_CLI.bat → CLI       │
                        └───────────────┬──────────────┘
                                        │
                        ┌───────────────▼──────────────┐
                        │  GUI/app.py   OR              │
                        │  run_argus_cli.py             │  ← builds the tool list
                        └───────────────┬──────────────┘
                                        │
                        ┌───────────────▼──────────────┐
                        │  core/safety.py               │  ← validates target first
                        │  (SafetyLayer)                │
                        └───────────────┬──────────────┘
                                        │
                        ┌───────────────▼──────────────┐
                        │  core/agent.py  (ArgusBrain)  │  ← the "brain": LangChain
                        │  ReAct agent + Ollama LLM     │    ReAct loop, decides steps
                        └───────────────┬──────────────┘
                                        │ calls tools
                        ┌───────────────▼──────────────┐
                        │  core/tools.py (WSLBridgeTools)│ ← the "hands": runs real
                        │  Reachability, Subdomains,     │   scans inside Kali (WSL)
                        │  Recon, XSS, SQLi, Nikto,      │
                        │  FFUF, Secrets, KnowledgeGraph │
                        └───────┬───────────────┬───────┘
                                │               │
             ┌──────────────────▼───┐   ┌───────▼───────────────┐
             │ core/memory.py       │   │ core/rag_kb.py         │
             │ (ArgusMemory)        │   │ (CVE / tech context)   │
             │ SQLite blackboard +  │   │ RAG knowledge base     │
             │ knowledge graph      │   └────────────────────────┘
             └──────────┬───────────┘
                        │
             ┌──────────▼───────────┐
             │ reports/report_engine │  ← final JSON + Markdown report
             │ .py (ReportEngine)    │
             └───────────────────────┘
```

**In one sentence:** the entry point builds a list of tools → `SafetyLayer` checks the
target is allowed → `ArgusBrain` (LLM) reasons step-by-step and calls `WSLBridgeTools`
to run real recon/scans inside Kali → results are stored in `ArgusMemory` (SQLite) and
enriched from `rag_kb` → `report_engine` writes the final report.

---

## 3. File-by-file: what each file does

### Entry points (how you start it)
| File | Role |
|------|------|
| `LAUNCH_STUDIO.bat` | Starts Ollama + WSL SSH, then runs the Streamlit web GUI on `http://localhost:12199`. |
| `LAUNCH_CLI.bat` | Interactive command-line launcher (asks for target + mode). |
| `run_argus_cli.py` | The actual CLI program. Builds the 10 tools, runs safety check, drives `ArgusBrain`. |
| `GUI/app.py` | The Streamlit web interface (same pipeline as the CLI, with a UI). |

### `core/` — the engine (this is the heart)
| File | Class / role |
|------|--------------|
| `core/agent.py` | `ArgusBrain` — the AI brain. LangChain **ReAct** agent talking to the Ollama LLM; decides which tool to run next and synthesizes the final report. |
| `core/tools.py` | `WSLBridgeTools` — the hands. Bridges Windows → Kali (WSL/SSH) and runs the real engines: reachability, subdomain enumeration, recon suite, XSS, SQLi, path traversal, Nikto, FFUF, secrets analysis, knowledge-graph queries, report generation. **(largest, most important file)** |
| `core/memory.py` | `ArgusMemory` — SQLite "blackboard": stores findings, subdomains, and the knowledge graph of relationships between targets. |
| `core/safety.py` | `SafetyLayer` — validates the target and mode before any scan runs (scope/allow-list guardrails). |
| `core/rag_kb.py` | RAG knowledge base — provides CVE and technology context (`get_tech_context`, `analyze_timeout_pattern`). |
| `core/schemas.py` | Pydantic models (`SecurityReport`, `PluginResult`) — the strict shape of the output. |
| `core/__init__.py` | Marks `core` as a Python package. |

### `reports/` — output
| File | Role |
|------|------|
| `reports/report_engine.py` | `ReportEngine` — turns findings into the final JSON + Markdown report. |
| `reports/__init__.py` | Package marker. |

### Config & data
| File | Role |
|------|------|
| `requirements.txt` | Python dependencies (LangChain, Streamlit, FAISS, paramiko, pydantic, …). |
| `.env.example` | Template for settings (WSL host/user/pass, Ollama host, model name). Copy to `.env` and edit. |
| `argus_intelligence.db` | The SQLite database used by `ArgusMemory` (findings history + knowledge graph). |
| `knowledge_base/` | Folder where RAG source documents live (starts empty). |

### Setup / install (`setup/`)
Windows + Kali install scripts (`Step_1..3`, `run_kali_setup.bat`, `setup_python_kali.sh`,
`argus_recon_fixed.sh`, `check_and_install.sh`). Used once to prepare the environment.

### Docs (`docs/`)
Master documentation, architecture (arc42/C4 `.docx`), core guides, and the project
language/standards file (`GEMINI.md`).

### Tests (`tests/`)
`run_all_tests.py`, `test_argus_comprehensive.py`, `test_xss_scanner.py`,
`_run_xss_live.py` — sanity/scanner tests.

### `sample_reports/`
A few example outputs so you can see what a finished report looks like (the original
repo had ~30 generated reports; only 3 samples were kept here to reduce clutter).

### `_experimental_advanced_modules/` (OPTIONAL — not required to run)
Unique, newer modules copied from the **GradProject** version. They are **not wired
into this runnable build** — kept here so nothing valuable is lost:
| File | What it adds |
|------|--------------|
| `llm_engine.py` | A custom (non-LangChain) Ollama engine + embedded SecLists. |
| `verifier.py` | `Verifier` — re-checks/validates findings to cut false positives. |
| `payload_encoder.py` | `PayloadEncoder` — WAF-bypass encoding/obfuscation of payloads. |
| `agent_payload_decider.py` | `AgentPayloadDecider` — LLM picks which payloads to use. |
| `agent.py` | `ArgusPipeline` — GradProject's alternative fixed-pipeline agent. |

---

## 4. Why this version (FINAL_STABLE) and not the others

The original repo contained **three overlapping copies** of the project — the main
cause of the confusion:

| Copy | Status | Evidence |
|------|--------|----------|
| **FINAL_STABLE_SECURITY_PROJECT** ✅ | The real, runnable production build → **used for this clean folder** | Root `LAUNCH_STUDIO.bat`, `INSTALL_EVERYTHING.bat`, and `run_argus_cli.py` all point to it. Has `requirements.txt`, `.env`, safety layer, full scanner suite, tests. |
| root `core/` + `GUI/` ❌ | Deprecated / old | Root `run_argus_cli.py` says literally: *"The legacy code in ./core/ and ./GUI/ is DEPRECATED… missing SafetyLayer, XSS/SQLi scanners, RAG, plugin system, report engine."* |
| `GradProject/` ⚠️ | Newer experimental fork | Bigger, more offensive features, **but** no `requirements.txt`, no `.env`, not referenced by any launcher. Its unique modules were preserved in `_experimental_advanced_modules/`. |

---

## 5. How to run this clean build

```bat
:: 1) one-time: create a virtual env and install deps
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

:: 2) copy .env.example to .env and edit values (WSL user/pass, model)
copy .env.example .env

:: 3) launch the web studio
LAUNCH_STUDIO.bat
:: ...or the CLI
LAUNCH_CLI.bat
```

Requirements outside this folder: **Ollama** running with the configured model, and
**WSL/Kali** with the recon tools installed (see `setup/` and `docs/`).

---

## 6. Security note
`.env.example` ships with placeholder Kali credentials (`kali/kali`). The original
`.env` in the old repo contained the same default credentials in plaintext — change
them and never commit a real `.env` to git.
