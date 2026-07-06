#!/usr/bin/env bash
# Canonical consolidation automation for the Argus repository.
#
# Executes the Cleanup Manifest from docs/ARCHITECTURE_AUDIT_REPORT.md (items C1-C7)
# and the code-convergence tasks in specs/012-spec-reconciliation/tasks.md (T025-T028).
#
# This script exists because those steps require BOTH file deletion and a runnable
# test suite (Ollama/faiss/langchain, Python 3.12), which were unavailable in the
# environment that authored the specs. Run it in a real dev checkout.
#
# SAFETY: dry-run by default. Nothing is deleted or moved unless you pass --apply.
# The one behavioral refactor (C4: brain/factory/workflow merge) is intentionally
# NOT automated - it is guided as a checklist, because it must be validated by
# running pytest after each step.
#
# Usage:
#   scripts/consolidate_canonical.sh            # dry-run (prints what it would do)
#   scripts/consolidate_canonical.sh --apply    # perform the safe deletions/moves
set -euo pipefail

APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

run() {
  echo "  \$ $*"
  if [ "$APPLY" -eq 1 ]; then eval "$@"; fi
}

echo "== Argus canonical consolidation (apply=$APPLY) =="
echo "Repo: $ROOT"
echo

# ---------------------------------------------------------------------------
# C2 (T025): remove deprecated RAG forwarders - only if nothing imports them.
# ---------------------------------------------------------------------------
echo "[C2] Deprecated RAG forwarders (processor.py / vectorstore.py / engine.py)"
FORWARDER_IMPORTS=$(grep -rInE "app\.core\.rag\.(processor|vectorstore|engine)\b" app scripts tests \
  --include=*.py 2>/dev/null | grep -viE "rag_engine|document_processor|vector_store" || true)
if [ -n "$FORWARDER_IMPORTS" ]; then
  echo "  SKIP: forwarders are still imported - migrate these first:"
  echo "$FORWARDER_IMPORTS" | sed 's/^/    /'
else
  for f in processor vectorstore engine; do
    [ -f "app/core/rag/$f.py" ] && run "git rm -f app/core/rag/$f.py"
  done
fi
echo

# ---------------------------------------------------------------------------
# C1: remove the nested self-duplicate of the repository (1.6 GB).
# ---------------------------------------------------------------------------
echo "[C1] Nested self-duplicate directory"
NESTED="Argus-Digilians-fix-copy-setup-to-scripts"
if [ -d "$NESTED" ]; then
  if git ls-files --error-unmatch "$NESTED" >/dev/null 2>&1; then
    echo "  WARNING: nested dir is git-tracked - inspect before removing."
  else
    run "rm -rf \"$NESTED\""
  fi
else
  echo "  OK: no nested duplicate present."
fi
echo

# ---------------------------------------------------------------------------
# C6/C7: tidy stray files and caches (already gitignored).
# ---------------------------------------------------------------------------
echo "[C6/C7] Stray files and caches"
[ -d ".pytest_cache" ] && run "rm -rf .pytest_cache"
[ -d "Plan md" ] && run "mkdir -p docs/history && git mv 'Plan md/Plan.md' docs/history/Plan.md && rmdir 'Plan md'"
mkdir -p docs/history 2>/dev/null || true
for note in QUICK_START_FIX.txt RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt REACT_FORMAT_ERROR_FIX.txt \
            REORGANIZATION_REPORT.txt STREAMLIT_JAVASCRIPT_FIX.txt STUDIO_QUICK_START.txt \
            JSON_PARSING_FIX.md PARSING_ERROR_FIX.md TESTING_JSON_FIX.md; do
  [ -f "$note" ] && run "git mv \"$note\" \"docs/history/$note\""
done
for stray in check_integration.py test_parsing_fix.py; do
  [ -f "$stray" ] && run "git mv \"$stray\" \"tests/$stray\""
done
echo

# ---------------------------------------------------------------------------
# C4 (T026-T028): brain/factory/workflow consolidation - GUIDED, not automated.
# ---------------------------------------------------------------------------
cat <<'GUIDE'
[C4] Brain / Factory / Workflow consolidation (MANUAL - validate with pytest):
  1. Repoint tests to canonical modules:
       tests/test_registry/test_brain_v2.py       -> app.core.agent.brain (ArgusBrain)
       tests/test_registry/test_agent_factory.py  -> app.core.agent.agent_factory
       tests/test_langgraph_workflow.py            -> app.core.agent.graph / state
  2. Merge ArgusBrainV2.dispatch() into ArgusBrain (app/core/agent/brain.py).
  3. Merge agent_factory_v2 into app/core/agent/agent_factory.py.
  4. Migrate app/core/workflow/{graph,state,prompts,hooks}.py into app/core/agent/;
     keep the Action parser only as the fallback behind format=json (ADR-13).
  5. Run: pytest -q   (MUST be green before deleting shadows)
  6. Then: git rm app/core/brain.py app/core/agent/brain_v2.py \
             app/core/agent/agent_factory_v2.py app/core/workflow/*.py
  Ref: specs/012-spec-reconciliation/tasks.md T026-T028; ADR-13/14/15.
GUIDE
echo

# ---------------------------------------------------------------------------
# Validation gates (run after applying).
# ---------------------------------------------------------------------------
echo "[VALIDATE] Running deterministic gates"
run "python scripts/validate_specs.py"
run "python scripts/validate_ascii.py"
run "python -m compileall -q app scripts tests || true"
echo
echo "Done. Re-run with --apply to perform the safe deletions/moves above."
echo "C4 remains manual and MUST be validated with pytest in a full runtime."
