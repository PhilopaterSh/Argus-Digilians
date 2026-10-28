# Argus Project — AI-Native Migration Audit

**Prepared by:** Senior AI Architect review
**Scope:** `D:\argus project\all in one`
**Date:** 2026-07-05
**Basis:** Direct read of the live source tree (`core/`, `reports/`, `GUI/`, `run_argus_cli.py`). Every "current logic" claim below cites the actual file and construct it is drawn from — nothing here is assumed.

> **Verification note (per project standards):** This audit describes only what is present in the code as read. Where I state a limitation, it is traceable to a named function, list, or regex in the repository. Recommendations (models, frameworks, phases) are engineering proposals and are labelled as such, not as facts about the current system.

---

## 1. Executive Summary

Argus today is a **deterministic security scanner wearing an AI jacket**. The genuinely intelligent parts are small and gated; the load-bearing logic is hardcoded Python: fixed payload arrays, regex signature matching, keyword-scored prioritisation, and a "knowledge base" that is a static dictionary rather than a retrieval system.

Three findings define the migration:

1. **The "brain" is a fixed pipeline, not an agent.** `core/agent.py` (`ArgusBrain.ask`) runs the same 13 steps in the same order every time. A second file, `core/agent_ai_driven.py`, attempts an LLM-as-controller loop but still leans on a hardcoded `_RECOMMENDED_ORDER` fallback and never reasons about *what it found* to change *what it does next*.

2. **The "RAG" is not RAG.** `core/rag_kb.py` is three Python dicts (`TECH_VULNS`, `PATTERN_RULES`, `ATTACK_HINTS`) matched by substring (`tech_key.lower() in ts`). There are no embeddings, no vector store, and no documents — even though `faiss` ships in `requirements.txt`. Knowledge is frozen at authoring time and only covers IIS/ASP.NET.

3. **Detection is signature/regex, so it only finds what was pre-imagined.** XSS, SQLi, path traversal, secrets, and subdomain discovery are all driven by fixed lists (`PAYLOADS`, `SQL_ERRORS`, `WIN_PAYLOADS`/`LIN_PAYLOADS`, `PARAM_WORDLIST`, `COMMON` prefixes). Novel endpoints, non-Latin contexts, custom error pages, and unusual stacks fall through.

**Post-transformation vision.** Argus becomes an **agentic, multi-model security platform**:

- A **planner/orchestrator agent** decides the next action from evidence, not from a step counter.
- **Specialist sub-agents** (Recon, Web-Vuln, Exploit-Reasoning, Reporting) own their domains and pass structured context on a shared blackboard (the SQLite memory already exists for this).
- A **real RAG layer** (vector store over CVE feeds, tech advisories, and prior Argus findings) replaces the static dict and updates without code changes.
- A **tiered model strategy**: fast/cheap Small Language Models (SLMs) for classification and routing on every request; a frontier LLM only for the hard reasoning steps (exploit chaining, false-positive adjudication, final narrative). This is what keeps token cost and latency sane.

Crucially, the deterministic scanners are **kept as tools**. The AI does not *replace* the network-facing code that sends payloads — it replaces the *decision-making* around them: which payload, which endpoint, is this reflection actually exploitable, what does this evidence mean, what next.

---

## 2. Comprehensive Audit Table

| # | Feature / Module | Current Legacy Script / Logic (file → construct) | Proposed AI-Native Alternative & Recommended Model / Framework |
|---|---|---|---|
| 1 | **Orchestration ("the brain")** | `core/agent.py` → `ArgusBrain.ask()` runs a hardcoded **13-step sequential pipeline** (`[1/13]…[13/13]`). Order never changes; findings don't alter the plan. | **Planner–executor agent graph** (LangGraph or an equivalent state machine). Orchestrator LLM emits a plan and revises it after each observation. Reuse the existing tool functions as graph nodes. **Model:** frontier LLM for planning (Claude / GPT-class) throttled to plan/replan moments only. |
| 2 | **"AI-driven" controller** | `core/agent_ai_driven.py` → `_decide_next()` asks a local Ollama model for the next tool, but on any parse failure falls back to `_RECOMMENDED_ORDER`; no evidence-conditioned branching. | Promote this file to the real controller: **structured tool-calling** (JSON schema / function-calling) instead of regex-parsing free text (`re.search(r"\{.*\}")`). Add evidence-conditioned routing (e.g. "SQL error seen → escalate to exploitation sub-agent"). **Model:** mid-tier LLM with native tool-calling. |
| 3 | **Target / domain extraction** | `core/tools.py` → `_extract_domain()` and `agent.py` → `_extract_target()` / `_parse_scan_pattern()`: regex + string slicing to pull a domain from prose; wildcard modes parsed by counting `/*`. | Keep the regex as a cheap first pass, but wrap ambiguous input in an **SLM intent parser** that returns structured scope `{targets, mode, depth, constraints}`. **Model:** SLM (e.g. Llama-3.x-8B / Phi-class / Haiku-tier) — sub-second, pennies. |
| 4 | **Subdomain enumeration** | `core/tools.py` → `enumerate_subdomains()`: crt.sh + a **14-item hardcoded prefix list** `COMMON = ["www","mail","api",…]`. | Keep crt.sh/DNS as tools; add an **LLM-generated candidate list** conditioned on the target's industry and tech (e.g. fintech → `payments`, `kyc`, `ledger`). **Model:** SLM to expand wordlists on the fly; cache results in memory. |
| 5 | **Target prioritisation** | `core/tools.py` → `prioritize_targets()`: fixed keyword tiers with magic scores (`CRITICAL +30`, `HIGH +20`, `MEDIUM +10`, `LOW_VALUE -10`; `www/ftp/mx -15`). | **Semantic risk scoring**: embed each host/endpoint and score attack-surface value with an SLM that sees context (headers, tech, path). Replaces brittle substring matching. **Model:** embedding model + SLM classifier. |
| 6 | **Parameter discovery** | `core/tools.py` → `_discover_parameters()`: HTML/JS crawl + a **~130-word static `PARAM_WORDLIST`** + Arjun-style length-diff. | Keep crawl + diff engine (it's good). Feed discovered JS/HTML to an **LLM param-miner** that infers likely parameters from code semantics rather than a fixed wordlist. **Model:** SLM over extracted JS; frontier LLM only for obfuscated bundles. |
| 7 | **Path traversal / LFI** | `core/tools.py` → `check_path_traversal()`: hardcoded `WIN_PAYLOADS`/`LIN_PAYLOADS`, `FIXED_PAYLOADS` endpoint list, `FILE_PARAMS` set, and OS-signature string matching (`root:x:`, `[boot loader]`). | **Context-aware payload selection**: agent picks/mutates payloads from detected OS + WAF behaviour (the timeout pattern is already computed). Move encoding-bypass logic out of the static `rag_kb` dict into an **exploit-reasoning sub-agent**. **Model:** LLM for payload strategy; deterministic sender unchanged. |
| 8 | **XSS detection** | `core/tools.py` → `check_xss()`: fixed `PAYLOADS`, `EXEC_SIGS`, `FIXED_XSS_ENDPOINTS`, `COMMON_PARAMS`, and regex `_classify()` for reflection context. | Keep injection/marker mechanics; replace `_classify()` regex with an **LLM reflection-context judge** that reads the response snippet and rules on exploitability (encoded vs. live, attribute vs. tag vs. JS context). Cuts false positives/negatives. **Model:** SLM for the judge call (one small prompt per reflection). |
| 9 | **SQL injection** | `core/tools.py` → `check_sqli()`: hardcoded `SQL_ERRORS` fingerprint list + 5 fixed `PAYLOADS` + `FIXED_ENDPOINTS`. Error-based only. | Add **boolean/time-based inference** driven by an agent that reads differential responses (no error string needed). LLM adjudicates "is this a real injection or a coincidental error". **Model:** SLM for adjudication; frontier LLM for building exploitation chains. |
| 10 | **Secrets analysis** | `core/tools.py` → `analyze_secrets()`: regex `PATTERNS` (email, AWS, Google key…) + hardcoded `_EMAIL_NOISE_DOMAINS` allowlist. | Keep high-precision regex (AWS/Google keys) as-is; add an **LLM secret-triage** pass for context-dependent leaks (tokens in JS, config fragments) that regex misses. **Model:** SLM classifier with a confidence gate. |
| 11 | **"RAG" knowledge base** | `core/rag_kb.py`: **static dicts** `TECH_VULNS`, `PATTERN_RULES`, `ATTACK_HINTS`; substring lookup in `get_tech_context()`. No embeddings despite `faiss` in `requirements.txt`. Covers only IIS/ASP.NET. | **Real vector RAG**: ingest NVD/CVE feeds, vendor advisories, ExploitDB, and prior Argus reports into a vector store (FAISS is already a dependency; or Chroma/Qdrant). Retrieve by semantic similarity to detected stack. Updatable without code edits. **Model:** embedding model + retrieval; LLM synthesises. |
| 12 | **LLM threat analysis** | `core/agent.py` → `_llm_threat_analysis()`: only fires when a scanner **already** confirmed a finding (`has_confirmed` gate); otherwise skipped. Single fixed 5-question prompt to Ollama. | Broaden to **evidence synthesis on every scan** with grounding constraints, driven by retrieved RAG context. Keep the anti-hallucination guard (tools remain the only evidence source) but let the model reason about *suspected* issues and next tests. **Model:** frontier LLM, called once per scan with retrieved context. |
| 13 | **Web / CVE search** | `core/tools.py` → `smart_web_search()`: DuckDuckGo tiers, then CVE regex `CVE-\d{4}-\d+` scraped from text. | Replace scrape-and-regex with **structured tool calls** to NVD/vuln APIs, results fed into RAG. LLM ranks relevance to the actual stack. **Model:** SLM for ranking; deterministic API client. |
| 14 | **Safety layer** | `core/safety.py`: regex `DESTRUCTIVE_PATTERNS`, `PRIVATE_RANGES`, char-strip `sanitize_input()`. Pure allow/deny. | **Keep the deterministic guardrails as the outer boundary** (do *not* hand safety to an LLM). Add an LLM **policy-reasoning layer inside** the boundary for scope/authorisation nuance, but the regex kill-switch stays authoritative. Defence-in-depth. |
| 15 | **Nikto / FFUF** | `core/tools.py` → `run_nikto()`, `run_ffuf_discovery()`: shell out to Kali via WSL. `_INFO_NIKTO` list separates info vs. findings by substring. | Keep as tools (they're external scanners). Replace the substring info/finding split with an **LLM finding-normaliser** that maps raw tool output to structured, deduplicated findings. **Model:** SLM. |
| 16 | **Report generation** | `reports/report_engine.py` + `agent.py` → `_dict_to_markdown()`: template string assembly; risk score parsed from JSON via regex (`meta.risk_score`). | **LLM report synthesiser** producing audience-tuned narratives (exec vs. engineer) from the structured findings, with deterministic scoring retained for auditability. **Model:** frontier LLM for narrative; keep numeric scoring deterministic. |

---

## 3. Architecture Deep Dive

### 3.1 From fixed pipeline to agent graph

Today, control flow is literally a numbered list inside `ArgusBrain.ask()` in `core/agent.py`. The target architecture inverts this: a **stateful graph** where the orchestrator decides transitions.

```
                         ┌────────────────────────────────────────┐
   User scope ─────────▶ │  INTENT / SCOPE PARSER  (SLM)          │
   (prose or wildcard)   │  → {targets, mode, depth, constraints} │
                         └──────────────────┬─────────────────────┘
                                            │
                         ┌──────────────────▼─────────────────────┐
                         │  SAFETY BOUNDARY (deterministic)       │  ← core/safety.py stays
                         │  regex kill-switch + scope allow-list   │    authoritative
                         └──────────────────┬─────────────────────┘
                                            │
                         ┌──────────────────▼─────────────────────┐
                         │  ORCHESTRATOR / PLANNER  (Frontier LLM) │
                         │  reads blackboard → picks next sub-agent│◀────────────┐
                         │  replans on new evidence                │             │
                         └───┬───────────┬───────────┬────────────┘             │
                             │           │           │                          │
              ┌──────────────▼─┐ ┌───────▼──────┐ ┌──▼───────────────┐          │
              │ RECON AGENT    │ │ WEB-VULN     │ │ EXPLOIT-REASONING │          │
              │ (SLM router)   │ │ AGENT (SLM   │ │ AGENT (Frontier   │          │
              │ subdomains,    │ │ judges       │ │ LLM: chaining,    │          │
              │ ports, params  │ │ reflections) │ │ FP adjudication)  │          │
              └───────┬────────┘ └──────┬───────┘ └────────┬─────────┘          │
                      │  calls existing deterministic TOOLS │                    │
                      │  (tools.py functions, unchanged)     │                   │
              ┌───────▼──────────────────▼────────────────────▼──────┐          │
              │  SHARED BLACKBOARD  = core/memory.py (SQLite)         │──────────┘
              │  findings + entities + knowledge graph (already here) │  evidence loop
              └───────────────────────┬──────────────────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │  RAG RETRIEVAL LAYER  (vector store) │  ← replaces rag_kb.py dict
                    │  CVE feeds, advisories, past reports  │
                    └─────────────────┬──────────────────┘
                                      │
                    ┌─────────────────▼──────────────────┐
                    │  REPORTING AGENT (Frontier LLM)      │
                    │  narrative + deterministic scoring    │  ← reports/report_engine.py
                    └──────────────────────────────────────┘
```

### 3.2 How context passes between agents

The good news: **the substrate for a multi-agent blackboard already exists.** `core/memory.py` (`ArgusMemory`) is a SQLite store of findings, entities, and a knowledge graph, and every tool already writes to it (`self.memory.add_finding(...)`, `upsert_entity`, `add_relation`). Sub-agents don't need to pass giant prompts to each other — they **read and write the blackboard**:

- **Recon Agent** writes discovered hosts/params/tech as entities; the **Orchestrator** reads the graph via the existing `query_knowledge_graph()` to decide whether to dispatch the Web-Vuln Agent.
- **Web-Vuln Agent** writes confirmed/suspected findings; the **Exploit-Reasoning Agent** subscribes to `severity="Critical"` findings (e.g. the SQLi write in `check_sqli()`) and only then spins up — no wasted frontier-LLM tokens on clean targets.
- **RAG retrieval** is keyed off the `tech` entity written during recon, so CVE context is fetched semantically instead of via `get_tech_context()`'s substring match.

This maps cleanly onto the current file layout under `D:\argus project\all in one`:

| Concern | Today | Target (same tree) |
|---|---|---|
| Orchestration | `core/agent.py` (fixed) / `core/agent_ai_driven.py` (partial) | `core/orchestrator.py` — LangGraph state machine; retire the 13-step version |
| Tools | `core/tools.py` (`WSLBridgeTools`) | Unchanged as **tool nodes**; wrap each with a structured schema |
| Sub-agents | — | `core/agents/recon.py`, `web_vuln.py`, `exploit.py`, `reporting.py` |
| Memory/blackboard | `core/memory.py` | Unchanged; add a `subscribe(severity)` helper |
| Knowledge | `core/rag_kb.py` (dict) | `core/rag/` — ingestion + vector store; keep dict as offline fallback |
| Safety | `core/safety.py` | Unchanged as outer boundary; add inner policy-reasoning |
| Reports | `reports/report_engine.py` | Keep scoring; add LLM narrative pass |

### 3.3 The existing `_experimental_advanced_modules/` are stepping stones

Per `PROJECT_MAP.md`, the repo already contains unused modules that fit the target design and should be wired in rather than rebuilt: `verifier.py` (false-positive re-checking → becomes the adjudication step), `payload_encoder.py` (WAF-bypass encoding → feeds the exploit agent), and `agent_payload_decider.py` (LLM picks payloads → the payload-selection node). Migrating these off the shelf de-risks Phase 2.

---

## 4. Cost vs. Latency Strategy (SLM vs. Frontier LLM)

The single biggest lever on both cost and latency is **not calling a frontier model when an SLM will do.** A scan touches dozens of endpoints; if every reflection-context judgement or param-mining call hit a frontier LLM, cost and wall-clock time would explode.

**Routing rule of thumb:**

- **SLM (fast, cheap, high-volume):** intent parsing, wordlist expansion, per-endpoint classification, XSS reflection judging, secret triage, Nikto/FFUF normalisation, relevance ranking. These are many small, well-scoped calls. Target: local Ollama SLM or a Haiku-tier hosted model, sub-second, fractions of a cent each.
- **Frontier LLM (slow, expensive, low-volume):** the planner's plan/replan decisions, exploit-chain reasoning, false-positive adjudication on Critical findings, and the final report narrative. Ideally **1–5 calls per scan**, not per endpoint.
- **No model at all (deterministic):** the actual payload sending, safety kill-switch, numeric risk scoring, DNS/port checks. Latency-free and auditable.

**Concrete tactics:**

1. **Gate frontier calls on severity.** The current `_llm_threat_analysis()` already gates LLM inference behind `has_confirmed`. Keep that instinct — extend it so the *expensive* model only engages when the blackboard holds something worth reasoning about.
2. **Cache aggressively.** Tech→CVE retrievals, expanded wordlists, and repeat-target decisions should hit the SQLite/vector cache, not the model. `agent_ai_driven.py` already refuses exact tool repeats — apply the same discipline to model calls.
3. **Batch classification.** Judge many reflections/params in one SLM prompt rather than one call each.
4. **Local-first for volume, hosted for depth.** Keep Ollama for the high-frequency SLM work (data stays on-prem, zero marginal cost — important for a security tool), and reserve hosted frontier tokens for the handful of deep-reasoning moments.

---

## 5. Implementation Roadmap (phased, non-breaking)

The guiding principle: **the deterministic scanners keep working the entire time.** Each phase adds an AI layer *around* stable tools, so the live system never depends on an unproven component.

**Phase 0 — Foundation & instrumentation (no behaviour change).**
Wrap every `WSLBridgeTools` method in a structured tool schema (name, input, output contract). Add tracing/token accounting. Freeze current outputs as regression fixtures using `tests/` and `sample_reports/`. Exit criterion: every tool callable via a uniform interface with logged latency/cost.

**Phase 1 — Real RAG replaces the static dict.**
Stand up the vector store (FAISS is already a dependency), ingest NVD/CVE + advisories + the existing `sample_reports/`, and make `get_tech_context()` a thin adapter over retrieval with the old dict as offline fallback. Lowest-risk, immediately widens coverage beyond IIS/ASP.NET. Exit criterion: retrieval returns relevant CVEs for a non-Microsoft stack that the dict cannot handle today.

**Phase 2 — Promote the agentic controller.**
Make `core/agent_ai_driven.py` the default, but upgrade `_decide_next()` from regex-parsed free text to native tool-calling, and add evidence-conditioned routing. Wire in `_experimental_advanced_modules/verifier.py` for false-positive adjudication. Keep `core/agent.py`'s fixed pipeline selectable as a fallback flag. Exit criterion: on the sample targets, the agent reorders/skips steps based on findings and matches or beats the fixed pipeline's findings with fewer wasted calls.

**Phase 3 — Specialist sub-agents + SLM judges.**
Split Recon / Web-Vuln / Exploit-Reasoning / Reporting into sub-agents on the shared blackboard. Replace the regex `_classify()` (XSS) and error-only SQLi logic with SLM judges. Introduce the SLM/frontier routing table from §4. Exit criterion: measurable false-positive reduction on `sample_reports/` targets and bounded frontier-call count per scan.

**Phase 4 — Reasoning-driven exploitation & adaptive payloads.**
Move payload selection/encoding out of static lists into the exploit agent (`payload_encoder.py`, `agent_payload_decider.py`). Add boolean/time-based SQLi inference. Frontier LLM builds exploitation chains from blackboard evidence. Exit criterion: Argus confirms at least one class of finding that the current signature-only approach misses.

**Phase 5 — Hardening & governance.**
Multimodal (screenshot reasoning for UI-driven findings), continuous RAG feed updates, human-in-the-loop gates on high-severity actions, and the inner policy-reasoning layer inside `safety.py`'s boundary. Exit criterion: full audit trail of every model decision, with the deterministic kill-switch still overriding everything.

Throughout, the outer `SafetyLayer` and the deterministic senders remain untouched, so a bad model decision can never turn into a destructive action — it can only mis-*prioritise*, which the human reviewer catches.

---

*Sources for all "current logic" claims: `core/agent.py`, `core/agent_ai_driven.py`, `core/tools.py`, `core/safety.py`, `core/rag_kb.py`, `core/memory.py`, `reports/report_engine.py`, `PROJECT_MAP.md`, `requirements.txt` — all within `D:\argus project\all in one`.*

*Verification checkpoint: Every statement about the current system in this document is traceable to a named construct in the files above and was read directly from source, not inferred. Model/framework recommendations are labelled proposals, not existing facts.*
