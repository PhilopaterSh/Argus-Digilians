# Argus Security Framework — Clean Build ("all in one")

A single, organized, **runnable** copy of the Argus AI Security Framework.
No nested duplicates, no scan artifacts, no caches — just the files that power the app.

**👉 Start here:** read [`PROJECT_MAP.md`](PROJECT_MAP.md) — it explains the whole
project end to end (what runs what) and lists every file's job.

## Run it
```bat
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      REM then edit values
LAUNCH_STUDIO.bat           REM web GUI at http://localhost:12199
```
Or CLI: `LAUNCH_CLI.bat`

## Layout
```
all in one/
├── PROJECT_MAP.md          ← read this first (full explanation)
├── LAUNCH_STUDIO.bat       ← start the web GUI
├── LAUNCH_CLI.bat          ← start the CLI
├── run_argus_cli.py        ← CLI program
├── requirements.txt
├── .env.example
├── argus_intelligence.db   ← memory DB (findings + knowledge graph)
├── core/                   ← the engine (agent, tools, memory, safety, rag, schemas)
├── GUI/                    ← Streamlit web interface
├── reports/                ← report engine (JSON + Markdown output)
├── knowledge_base/         ← RAG documents (empty by default)
├── setup/                  ← install scripts (Windows + Kali)
├── docs/                   ← documentation + architecture
├── tests/                  ← test scripts
├── sample_reports/         ← example finished reports
└── _experimental_advanced_modules/  ← OPTIONAL newer modules (not required to run)
```

Built from `FINAL_STABLE_SECURITY_PROJECT` — the version every original launcher
actually used. See `PROJECT_MAP.md` §4 for why.
