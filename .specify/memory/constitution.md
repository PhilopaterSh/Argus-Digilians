<!--
Sync Impact Report
==================
Version change: 1.4.0 -> 1.6.0 (MINOR: additive graph-verified-structure principle;
PATCH: descriptive project-phase note; MINOR: broadened commit-discipline trigger scope)

Amendment 2026-07-23c (specs/025 benchmark-suite implementation session):
Extended principle (no principle added/removed, existing NON-NEGOTIABLE principle's scope
broadened):
- X. Traceable Commit Discipline - trigger widened from "resolved defect or completed fix"
  to "any completed and verified unit of work" (a shipped feature/task, a tooling/dependency
  integration, a documentation/research pass, a spec-kit governance amendment), with an
  explicit "verified working, not just written" gate and an explicit note that one session
  covering several unrelated units of work produces several commits, not one.
Rationale: this session completed several large, unrelated, individually-verified units of
work in sequence (the graphify integration, the ExploitGym research documentation, the `019`
status-desync fix, and the full `specs/025` benchmark-suite implementation including a
live-verified WSL-networking bug fix) with nothing committed yet by the time this amendment
was requested. The user explicitly asked for a standing rule that a successful, complete, and
organized step MUST be followed by a git commit with a descriptive name/message, and for
that rule to live in spec-kit governance, not only in conversation. Principle X already
existed and already carries the correct non-negotiable weight and human-confirmation
safeguard, but its literal wording ("resolved defect or completed fix") is narrower than what
actually happened this session - none of the four items above are "fixes" in the literal
sense. Broadening the trigger wording closes that gap without re-litigating the
already-settled human-approval gate or duplicating a second principle for the same concern
(Constitution IX's own single-source-of-truth discipline applied to the Constitution itself).
Templates requiring updates:
- .specify/templates/plan-template.md        -> no change (Constitution Check gate already generic)
- .specify/templates/spec-template.md        -> no change
- .specify/templates/tasks-template.md       -> no change
- .opencode/commands/speckit.constitution.md -> no change (agent-neutral)
Follow-up TODOs: none - this session's own accumulated uncommitted work (see above) is the
first case meant to be committed under the broadened wording, pending the user's per-commit
confirmation per Principle X's existing human-approval gate.

Amendment 2026-07-23b (graphify integration session, continued):
Extended section (no principle added/removed):
- "Security & Operational Constraints" -> added project-phase status note
Rationale: while reviewing the graphify/installer boundary decision, the user noted that
Argus is still in active development and has not yet reached a general end-user release -
this project-phase fact is *why* Principle II's installer boundary and Principle XII's
dev-only graphify placement matter now even though most current work is dev-facing, not
end-user-facing. Recording it here keeps that context durable rather than living only in
this session's conversation, per the same provenance discipline Principle XI already
requires for research findings.
Templates requiring updates: none.
Follow-up TODOs: revisit/update this status note when the project reaches a
general-release milestone.

Amendment 2026-07-23 (graphify integration session):
Added principle (additive only; no existing principle redefined or removed):
- XII. Graph-Verified Structure (NON-NEGOTIABLE)
Extended section:
- "Development Workflow & Quality Gates" -> added Structure gate
New dependency:
- `graphifyy` added to a new, standalone `config/requirements-graphify.txt` (PyPI package
  name; CLI command is `graphify`) - deliberately NOT added to `config/requirements.txt`,
  `config/requirements-dev.txt`, or `scripts/ARGUS_INSTALLER.ps1`'s embedded requirements,
  so the graph is reproducible on demand (`pip install -r
  config/requirements-graphify.txt`) without being pulled into every CI job (`ci.yml`
  installs `requirements-dev.txt` in 4 uncached jobs; `graphify` and its ~30 tree-sitter
  packages are never invoked there) or into the single-source end-user installer, which
  Principle II requires to stay self-contained with only the runtime deps Argus itself
  needs.
Rationale: this session installed `graphify` (local AST + optional-LLM knowledge-graph
extraction) and produced the repository's first full structural map (1929 nodes, 3566
edges, 168 labeled communities), which surfaced real architectural hubs
(`WSLBridgeTools`, `ArgusBrain`, `ArgusMemory`, ...) and existing groupings that would
otherwise have to be rediscovered by inspection every time. The user explicitly asked
for this to become a standing reference consulted before adding new files or
reorganizing existing ones - "every time," not a one-off exercise - which is the same
durable-artifact requirement Principle IX already applies to duplication checks and
Principle XI already applies to research findings. Left undocumented, the graph would
have the same fate research findings had before XI: useful once, in conversation, then
unrecoverable. `graphifyy` was initially placed in `config/requirements-dev.txt`; moved
to its own file the same session after review showed that file is installed by 4 CI jobs
with no pip cache, which would have added real, repeated, functionally-useless install
cost to every push - the same "don't add what a step will never use" discipline
Principle II already applies to the installer.
Templates requiring updates:
- .specify/templates/plan-template.md        -> no change (Constitution Check gate already generic)
- .specify/templates/spec-template.md        -> no change
- .specify/templates/tasks-template.md       -> no change
- .opencode/commands/speckit.constitution.md -> no change (agent-neutral)
Follow-up TODOs: none - `graphify-out/` already added to `.gitignore` and `graphifyy`
already isolated in `config/requirements-graphify.txt` this same session.

Amendment 2026-07-13 (multi-agent/browser-automation research session, fix/copy-setup-to-scripts):
Added principle (additive only; no existing principle redefined or removed):
- XI. Documented Research Provenance (NON-NEGOTIABLE)
Rationale: this session's `specs/020` (multi-agent role separation) and `specs/022`
(browser automation) decisions were both directly shaped by external web research
(local-model VRAM/latency limits, abliteration's measured effect on model quality,
AI-Browser-Agent-vs-headless-browser tradeoffs) that was cited in chat but not
initially written into any durable project artifact - the same unaudited-reasoning
gap Principle V already forbids for installer logs and Principle X already closed
for uncommitted fixes. The user explicitly requested this be made a standing,
mandatory rule (findings documentation described as necessary and important), not a one-time
cleanup. `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`'s new "10. Research References"
section and the `specs/020`/`022` `research.md` addenda are the first artifacts
produced under this principle.
Templates requiring updates:
- .specify/templates/plan-template.md        -> no change (Constitution Check gate already generic)
- .specify/templates/spec-template.md        -> no change
- .specify/templates/tasks-template.md       -> no change
- .opencode/commands/speckit.constitution.md -> no change (agent-neutral)
Follow-up TODOs: none - already applied retroactively to this session's `020`/`022`
research (see `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` section 10 and the two specs'
`research.md` files).

Amendment 2026-07-08b (repo-hygiene session, fix/copy-setup-to-scripts):
Added principle (additive only; no existing principle redefined or removed):
- X. Traceable Commit Discipline (NON-NEGOTIABLE)
Extended section:
- "Development Workflow & Quality Gates" -> added Commit gate (and, retroactively
  for the same-day IX amendment, Duplication gate)
Rationale: this session's fixes were repeatedly staged but left uncommitted
across many turns pending user confirmation - safe for reversibility during
active work, but if never explicitly finalized, git history stops being a
truthful record of what was actually resolved and when, undermining the same
auditability Principle V already requires of installer logs. This principle
extends that same auditability expectation to source control: every resolved
defect/completed fix MUST end in a commit, with one commit per coherent unit
of work and a message stating why, not just what. It explicitly does NOT
override the human-approval gate an AI coding assistant operates under - it
mandates the end state (a clean, descriptive commit exists), not that an
agent may execute `git commit` unattended.

Amendment 2026-07-08 (repo-hygiene session, fix/copy-setup-to-scripts):
Added principle (additive only; no existing principle redefined or removed):
- IX. Single Source of Truth - No Duplication (NON-NEGOTIABLE)
New enforcement tool:
- scripts/check_duplication.py (exact-file-hash and normalized-function-body
  detection; --diff mode for CI, --all mode for full-repo reporting)
Rationale: this session found, by direct inspection (not estimation), a
byte-identical Setup/requirements.txt vs scripts/Setup/requirements.txt, an
identical `_build_target_url`/`_first_web_port` pair independently defined in
both app/core/agent/nodes/scanner.py and exploit.py, an identical DB-connection
helper (`_get_conn`/`_get_gui_conn`) independently defined in two GUI utility
files, and a divergent pair (workspace/run_argus_cli.py vs
scripts/run_argus_cli.py) that started as one file and silently forked because
nothing forced reconciliation. Principle II already forbade duplication within
the installer specifically; Principle VII already required one canonical
authority for cross-cutting *design decisions*; neither covered general
file/code duplication. This amendment closes that gap the same way VII and
VIII closed theirs.

Amendment 2026-07-05 (post Spec Consolidation):
Added principles (additive only; no existing principle redefined or removed):
- VII. Canonical Reconciliation Authority (NON-NEGOTIABLE)
- VIII. Truthful Runtime (No Fabrication) (NON-NEGOTIABLE)
Extended section:
- "Development Workflow & Quality Gates" -> added Testing & AI-Evaluation Gate
Rationale: the 012-spec-reconciliation consolidation and the 010 agent design
established, de facto, (a) a single canonical source of truth, (b) a no-fabrication
runtime rule, and (c) unit/integration/e2e/AI-eval test tiers. These were not yet
encoded as constitutional principles; this amendment closes that gap.

Original 1.0.0 ratified set (unchanged):
- I. Admin-First Elevation (NON-NEGOTIABLE)
- II. Single-Source Installer
- III. Idempotent & Test-Gated (NON-NEGOTIABLE)
- IV. Platform-Boundary Clarity
- V. Observability & Logging
- VI. English-Only Documentation

Templates requiring updates:
- .specify/templates/plan-template.md        -> no change (Constitution Check gate already generic)
- .specify/templates/spec-template.md        -> no change
- .specify/templates/tasks-template.md       -> no change
- .opencode/commands/speckit.constitution.md -> no change (agent-neutral)

Follow-up TODOs: none - specs/checklist.md CHK058-063 already added (2026-07-08)
tracking the 5 duplicate groups found this session through to resolution.
-->

# Argus Security Framework Constitution

## Core Principles

### I. Admin-First Elevation (NON-NEGOTIABLE)

Any script that modifies the host operating system, Windows features, WSL, or the
network configuration MUST self-elevate to Administrator before performing a single
mutating action. Warning the user and continuing without elevation is forbidden.

Rules:
- The installer MUST detect non-admin execution and re-launch itself elevated,
  preserving all original arguments.
- If elevation is declined, the script MUST abort with a clear, actionable message
  and a non-zero exit code. It MUST NOT degrade into a partial run.
- Re-elevation is allowed exactly once, at the very start of execution.

Rationale: a mid-way failure because a privileged step hit a permission wall leaves
the environment half-configured and is the primary source of broken Argus installs.

### II. Single-Source Installer

There MUST be exactly one authoritative entry point that installs, configures, and
validates the full Argus environment. Fragmented multi-file orchestration that
duplicates prerequisite checks across steps is forbidden.

Rules:
- `scripts/ARGUS_INSTALLER.ps1` is the single source of truth for installation.
- A root-level `INSTALL.bat` exists only as a convenience launcher; it MUST NOT
  contain installation logic of its own.
- Each prerequisite (Python, Ollama, WSL, Kali) MUST be checked exactly once and
  its result reused by every downstream step. Duplicate checks across files are a
  defect.

Rationale: distributed, duplicated logic (the legacy `Setup/Step_*.bat` chain)
causes version drift, path-resolution fragility, and inconsistent behavior.

### III. Idempotent & Test-Gated (NON-NEGOTIABLE)

Every installation step MUST be safe to re-run, and the pipeline MUST be gated so a
failed critical step halts before it cascades.

Rules:
- Every step MUST check whether its target is already satisfied before acting, and
  skip cleanly if it is. Re-running the installer on a healthy system MUST produce
  no errors and no redundant work.
- Steps are ordered by the critical dependency chain (Python -> Ollama -> WSL2 ->
  Kali -> venv -> tools -> SSH). A CRITICAL step that fails MUST abort the run; a
  NON-CRITICAL step that fails MUST be recorded as a warning and must not block the
  final health check.
- The pipeline MUST end with a health check that verifies all key components, and
  this health check MUST be embedded in the installer (no separate manual script
  required).

Rationale: operators re-run installers constantly (after reboots, after fixes).
A non-idempotent installer forces a full clean-up before every retry.

### IV. Platform-Boundary Clarity

Windows-host logic and Kali-guest logic MUST stay strictly separated, with the WSL
bridge as the only permitted crossing point.

Rules:
- Windows-side operations (PowerShell / Batch) MUST NOT assume a Linux tool is
  available on the host, and vice versa.
- Kali-side logic lives in shell scripts run via WSL (e.g. `check_and_install.sh`);
  it MUST be invoked as root inside the target distro and MUST receive only a
  translated WSL path (`/mnt/...`), never a raw Windows path.
- SSH (port 22) is the designated application-level bridge into Kali; tools and
  launchers MUST rely on it rather than ad-hoc command plumbing.

Rationale: confusing the two execution domains causes silent path errors and
permission failures that are extremely hard to diagnose.

### V. Observability & Logging

Installation and launch flows MUST produce an auditable record of every action and
its outcome.

Rules:
- The installer MUST write a timestamped log file under `logs/` for every run, in
  addition to console output.
- Every step MUST record a structured result (step id, name, status, detail) that
  feeds a final summary table.
- Launch scripts MUST report which engine mode (GPU/CPU) and which bridge state
  they are starting in, so a failed boot can be traced.

Rationale: when an install "mostly works", the log is the only artifact that lets
an operator see which component is the holdout.

### VI. English-Only Documentation

All documentation, comments, log messages, and user-facing strings MUST be written
in professional, technical English.

Rules:
- Code comments, README files, and Spec-Kit artifacts MUST be in English.
- Console output and log lines MUST be ASCII-safe English.
- No mixed-language files; no placeholder or template tokens left in committed
  documentation.

Rationale: mixed-language and placeholder-laden docs are unreadable to most
contributors and tools, and signal an unfinished artifact.

### VII. Canonical Reconciliation Authority (NON-NEGOTIABLE)

There MUST be exactly one canonical source of truth for cross-cutting design
decisions (module/package/class naming, ports, language version, RAG embedding/index
design, agent design, output parsing, testing, CI/CD).

Rules:
- `specs/012-spec-reconciliation` is that canonical source. When any spec, plan, ADR,
  architecture document, or code conflicts with it, `012` wins and the other artifact
  MUST be updated or marked `Superseded By` / `Deprecated` / `Replaced By`.
- New features MUST reference `012` for cross-cutting names and constants rather than
  reintroducing local variants.
- Superseded artifacts MUST NOT be silently deleted; they carry a resolving header
  pointing at the canonical replacement.

Rationale: incremental, unreconciled specs previously produced duplicate numbering,
divergent module names, and conflicting constants. A single authority prevents drift.

### VIII. Truthful Runtime - No Fabrication (NON-NEGOTIABLE)

Runtime code MUST NOT fabricate results. Any simulation, stub, or fallback that
invents data (e.g. synthetic open ports, fake scan/exploit success) is permitted only
in tests or an explicit demo mode, never in the production execution path.

Rules:
- Every node/tool MUST report real success, real failure, or an explicit
  dependency-unavailable state - never a fabricated success.
- Fallback behavior MUST degrade honestly (e.g. RAG-disabled when the pinned embedder
  is unavailable) and MUST surface the degraded state, not mask it.
- Demo/simulation flows MUST be isolated from production flows and clearly labeled.

Rationale: an autonomous agent whose runtime invents findings is worse than useless;
truthful state is the foundation of trustworthy automation and debuggability.

### IX. Single Source of Truth - No Duplication (NON-NEGOTIABLE)

No file, dependency manifest, or function/module logic MAY exist in more than one
place in the repository. Every responsibility MUST have exactly one canonical
implementation; every other location that needs it MUST import/reference the
canonical one, never re-derive or hand-copy it.

Rules:
- Before adding a new file or function, an author MUST check whether an existing
  one already serves the same purpose (`scripts/check_duplication.py --all`).
  Copy-pasting an existing implementation into a new location is forbidden; the
  existing one MUST be imported/reused, or factored out into a shared location if
  it isn't already importable from where it's needed.
- Any two files with byte-identical content are a defect: one MUST be deleted
  and replaced with a reference to the other (or, if both must physically exist
  for a build/deploy reason, one generates the other rather than both being
  hand-maintained).
- Any two functions implementing the same logic independently are a defect,
  regardless of naming - MUST be consolidated into one shared function.
- `scripts/check_duplication.py --diff <base_ref>` MUST run in CI (stage 1:
  diff-scoped, blocks new duplication without retroactively failing on the
  existing backlog - same staged rollout already used for `ruff.toml` and
  `mypy.ini`, per Constitution amendment precedent).
- Existing duplication found MUST be tracked to resolution in `specs/checklist.md`
  as a CHK item, not left open indefinitely; it MUST NOT be rediscovered from
  scratch in a future audit because no one recorded it the first time.
- A file that must temporarily exist as a compatibility shim for a canonical
  rename (e.g. Principle VII's superseded-artifact pattern) MUST say so
  explicitly in a header comment pointing at the canonical replacement - it is
  not exempt from this principle, it is a documented, time-boxed exception to it.

Rationale: this session found, by direct code inspection, an identical
`requirements.txt` hand-maintained in two places, an identical URL-building
helper independently defined in two agent nodes, an identical DB-connection
helper independently defined in two GUI utilities, and a CLI entrypoint that
started as one file and silently forked into two different tool sets because
nothing forced reconciliation when it drifted. Undetected duplication doesn't
just waste space - it rots: one copy gets fixed, the other doesn't, and the
next person to touch either has no way to know the other exists.

### X. Traceable Commit Discipline (NON-NEGOTIABLE)

Every resolved defect, completed fix, or other completed and verified unit of
work - a shipped feature/task, a tooling or dependency integration, a
documentation/research pass, a spec-kit governance amendment - MUST end in a
git commit that records it. Work that is finished but never committed does
not exist as far as the project's audit trail is concerned, and defeats the
observability this Constitution otherwise requires.

Rules:
- Once a unit of work is verified working and organized (tests pass, and
  live-verified where the work claims a live-environment result), it MUST be
  committed - not left staged indefinitely across unrelated further work, and
  not silently dropped. "Verified working" is the trigger, not "written" -
  half-finished or not-yet-checked work is not yet a commit candidate.
- Each commit MUST correspond to one coherent, reviewable unit of resolved
  work; unrelated fixes MUST NOT be squashed into a single commit (this
  project's own history - e.g. splitting the WAF/CDN pipeline fix, the
  containerized-lab feature, and the installer hardening into three separate
  commits in one session - is the standard to follow, not the exception). A
  single working session commonly produces several such commits, not one big
  one, when it covers several unrelated units of work (e.g. a tooling
  integration, a documentation pass, and a feature implementation in the same
  session are three commits, not one).
- Commit messages MUST state why the change was needed, not merely what
  changed - restating the diff in prose is not sufficient.
- Where a commit resolves a tracked item (a `specs/*/tasks.md` task or a
  `specs/checklist.md` CHK id), the commit message SHOULD reference it, so
  git history and Spec-Kit tracking stay cross-referenced.
- This principle governs the required END STATE - a clean, descriptive commit
  must eventually exist for every completed unit of work. It does NOT
  authorize an AI coding assistant to execute `git commit` without the human
  operator's explicit, per-instance confirmation; that human-approval gate is
  a separate, standing operational control this Constitution does not
  override. An assistant operating under this principle MUST still
  stage/prepare commits and request confirmation before writing them.

Rationale: mid-session, fixes are routinely kept staged-but-uncommitted while
work continues - correct for reversibility, but if a session ends without
ever finalizing them, the git history silently stops reflecting what was
actually fixed and when, which is exactly the kind of unaudited state
Principle V forbids for installer logs. This principle extends that same
auditability expectation to source control itself.

### XI. Documented Research Provenance (NON-NEGOTIABLE)

Any external research performed to inform a design decision (web search, literature review,
benchmark/documentation lookup) MUST have its findings and sources recorded in a durable project
artifact. Citing a source in conversation only, with no artifact update, does not satisfy this
principle.

Rules:
- Every research pass that materially informs an architecture decision, a spec, or a code
  change MUST be written into the relevant `specs/<phase>/research.md` (as a dated addendum if
  the spec already exists) or, for research that spans multiple phases or informs general
  architecture direction, into `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`'s "Research References"
  section.
- Sources MUST be recorded as direct links, not paraphrased without attribution - a future
  reader must be able to independently verify the finding, not just trust the summary.
- A decision that cites research without a recorded source is treated the same as Principle
  VIII's fabrication concern: an unverifiable claim presented as settled fact.
- This applies to every future research pass without exception, not only ones a reviewer
  happens to notice were uncited.

Rationale: this session's multi-agent architecture and browser-automation decisions were both
directly shaped by external research (local-model resource limits, measured model-quality
tradeoffs, AI-agent-vs-plain-tool design patterns) that existed only in conversation until
written down - the same unaudited-reasoning gap Principle V already forbids for installer logs
and Principle X already closed for uncommitted fixes. Undocumented research rots exactly like
undocumented code duplication (Principle IX): the reasoning behind a decision becomes
unrecoverable once the conversation that produced it is gone.

### XII. Graph-Verified Structure (NON-NEGOTIABLE)

A generated dependency/structure graph MUST be the reference consulted before adding a
new file or deciding how to reorganize existing ones - not memory, naming convention, or
a directory listing alone.

Rules:
- The graph MUST be produced by `graphify extract .` (local AST parsing; `--code-only`
  requires no API key or LLM backend) and, when a backend is available, enriched with
  `graphify label . --backend=<backend>` for human-readable community names. `graphify
  update .` refreshes it incrementally after code changes at no API cost.
- Before adding a new file, an author (human or AI assistant) MUST check the graph for an
  existing node or community already covering the same responsibility - via `graphify
  query "<question>"`, `graphify explain "<Name>"`, or the `graphify-out/graph.html`
  visualization - before deciding where the new file belongs. This is the structural
  counterpart to Principle IX's duplication check, applied before the fact rather than
  after.
- Before any reorganization pass, `graphify god-nodes` (architectural hubs) and the
  community list in `graphify-out/GRAPH_REPORT.md` MUST be reviewed so the new placement
  respects existing groupings instead of splitting one community across unrelated
  directories.
- `graphify-out/` is generated build output, not source: it MUST NOT be hand-edited, MUST
  stay out of version control, and MUST be regenerated - never manually reconciled - after
  structural changes so it cannot silently go stale.
- A graph built from a commit other than the current `HEAD` (see `GRAPH_REPORT.md`'s
  "Graph Freshness" section) MUST be treated as advisory only, not authoritative, until
  refreshed.

Rationale: this session used `graphify` to produce the repository's first full structural
map and found it materially useful for locating where a responsibility already lives
before adding to it. The user explicitly requested this become a standing reference
consulted every time for new files and reorganization decisions, not a one-off exercise -
the same durable-reference intent Principle IX already applies to duplication and
Principle XI already applies to research findings. Without this principle, the map
degrades into an unreferenced one-time artifact the same way ad-hoc research and ad-hoc
duplication checks did before being codified.

## Security & Operational Constraints

- **Target platform:** Windows 10 (build 19041+) or Windows 11, with WSL2 and a
  `kali-linux` distribution. The framework is authorized for defensive security
  testing, CTF, and educational use cases only.
- **Hardware floor:** 8 GB RAM minimum (16 GB+ recommended for AI models), 20 GB+
  free disk on the project drive. The installer MUST warn (not abort) when below
  these thresholds, except for model pulls which MUST be guarded by disk space.
- **AI engine:** Ollama, default model `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest`.
  The model name and pull-retry count MUST be overridable via environment variables
  (`ARGUS_MODEL`, `ARGUS_MODEL_PULL_RETRIES`, `ARGUS_MODEL_MIN_GB`).
- **Offline mode:** The installer MUST support an `-Offline` mode that skips every
  network download and clearly reports what the operator must provision manually.
- **Virtual environment:** Python dependencies MUST live in the isolated
  `Argus_venv/` at the project root; the system Python MUST NOT be polluted.
- **Project phase:** Argus is currently in active development (pre general-release); most
  work targets the development/contributor experience, not yet a polished general
  end-user release. This is part of why the installer boundary (Principle II) and the
  dev-only placement of tooling like `graphify` (Principle XII) matter now:
  `scripts/ARGUS_INSTALLER.ps1`'s embedded requirements target the eventual end-user
  install, while dev-only tooling stays outside it. Update this note when the project
  reaches a general-release milestone.

## Development Workflow & Quality Gates

- **Spec-Kit workflow:** Feature work follows `constitution -> specify -> clarify ->
  plan -> tasks -> implement -> analyze`. No implementation step may begin without
  an approved spec and plan.
- **Syntax gate:** Any PowerShell change MUST pass parser validation
  (`[System.Management.Automation.Language.Parser]::ParseFile`) with zero errors
  before it is considered done.
- **Dry-run gate:** The installer MUST expose a `-DryRun` mode that exercises the
  full control flow and path resolution without mutating the system; it is used to
  validate changes safely.
- **Legacy retention:** Deprecated `Setup/Step_*.bat` scripts are retained as a
  manual debugging fallback but are no longer the supported path. New logic goes
  into the single installer.
- **Testing & AI-Evaluation gate:** Per `012-spec-reconciliation` §6, changes MUST be
  covered by the appropriate tier - unit (mocked), integration (real Ollama + ephemeral
  SQLite + FAISS), end-to-end smoke, and - for RAG/agent changes - AI-evaluation
  (retrieval recall@k + faithfulness; agent bounded-loop termination). Every fixed
  defect MUST gain a regression test. CI runs these tiers (`012` §7).
- **Review gate:** All PRs/reviews MUST verify compliance with these principles;
  any deviation MUST be justified and documented in the plan's Complexity Tracking.
- **Duplication gate:** `scripts/check_duplication.py --diff <base_ref>` MUST run
  in CI per Principle IX; a PR introducing new file or function duplication
  MUST fail this gate until consolidated.
- **Commit gate:** Per Principle X, a PR/session MUST NOT be considered done while
  a verified fix remains uncommitted; an AI assistant MUST request explicit
  confirmation before each `git commit` rather than batching or auto-committing.
- **Research provenance gate:** Per Principle XI, a research-informed decision MUST NOT
  be considered done while its findings/sources exist only in conversation; the relevant
  `specs/<phase>/research.md` addendum or `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` §10
  entry MUST exist before the decision is treated as settled.
- **Structure gate:** Per Principle XII, `graphify-out/graph.html` and
  `graphify-out/GRAPH_REPORT.md` MUST be regenerated (`graphify update .` or `graphify
  extract .`) and consulted before a PR/session that adds new files or reorganizes
  existing ones is considered done.

## Governance

This Constitution is the highest-authority artifact for Argus development decisions
and supersedes any conflicting guidance in README files or older documentation when
a conflict exists.

Amendment procedure:
- Amendments require a documented rationale, a version bump per semantic versioning
  (MAJOR for principle removal/redefinition, MINOR for additions/expansions, PATCH
  for clarifications), and an updated Sync Impact Report at the top of this file.
- A ratified amendment MUST be propagated through the dependent templates listed in
  the Sync Impact Report.

Compliance review: every `/speckit.plan` invocation runs a Constitution Check gate;
violations MUST be either resolved or explicitly justified in the plan's Complexity
Tracking table before implementation begins.

**Version**: 1.6.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-07-23
