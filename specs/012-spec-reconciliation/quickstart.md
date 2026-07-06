# Quickstart: Verifying Spec Consolidation & Reconciliation

**Phase**: 1 - Validation | **Date**: 2026-07-05 | **Spec**: `specs/012-spec-reconciliation/spec.md`

---

## Purpose

This quickstart is a runnable validation guide. It confirms the repository conforms to the canonical
decisions in `spec.md`. Every check is read-only and safe to run repeatedly. These checks are the
manual form of the CI spec/doc-validation stages (`spec.md` section 7).

## Prerequisites

- Python 3.12 (canonical per `spec.md` section 2.6). The checks below use only the standard library.
- Run from the repository root.

---

## Check 1: No duplicate spec numbers

```bash
ls -1 specs | grep -oE '^[0-9]+' | sort | uniq -d
```

**Expected**: no output (empty). A printed number means a numbering collision remains.

---

## Check 2: Canonical runtime constants

```bash
# Port must be 12199 in config.yaml and the get_port fail-safe
grep -n "port:" config.yaml
grep -n "12199" scripts/get_port.py

# Python version must read 3.12 (no "3.10+") in specs
grep -rIn "3.10+" specs && echo "FOUND 3.10 (should be none)" || echo "OK: no 3.10+"
```

**Expected**: `config.yaml` -> `port: 12199`; `get_port.py` contains `12199`; no `3.10+` in specs
(except the `012` alias table that documents it as superseded).

---

## Check 3: Canonical naming only (no superseded module names in use)

```bash
# Superseded RAG short names must not be IMPORTED anywhere in first-party code
grep -rInE "from app\.core\.rag\.(processor|vectorstore|engine) import|import app\.core\.rag\.(processor|vectorstore|engine)\b" app scripts tests
```

**Expected**: no output. The forwarder files may still exist (pending deletion, `tasks.md` T025) but
nothing imports them.

---

## Check 4: Supersession markers resolve

```bash
grep -rIl "Superseded By\|Refined By\|Replaced By\|Partially Superseded" specs
```

**Expected**: the affected specs (`001`, `004`, `009`, `010`, `013`) are listed; open each and confirm
the marker names a canonical target (a `012` section, `010`, or `011`).

---

## Check 5: English-only / ASCII-safe first-party code

```bash
python3 - <<'PY'
import os
roots=['app','scripts','tests']; skip=('Argus_venv','node_modules','.git','__pycache__','.opencode')
exts=('.py','.bat','.ps1','.sh','.yaml','.yml')
bad=0
for r in roots:
    for dp,dn,fn in os.walk(r):
        dn[:]=[d for d in dn if d not in skip]
        for f in fn:
            if f.endswith(exts):
                p=os.path.join(dp,f)
                if any(c>=128 for c in open(p,'rb').read()):
                    print("NON-ASCII:",p); bad+=1
print("RESULT:", "CLEAN" if not bad else f"{bad} files dirty")
PY
```

**Expected**: `RESULT: CLEAN`. Intentional Unicode test data in `tests/test_memory.py` is stored as
`\uXXXX` escapes, so the source bytes stay ASCII while runtime values are unchanged.

---

## Check 6: Syntax integrity

```bash
python3 - <<'PY'
import os,py_compile
roots=['app','scripts','tests']; skip=('Argus_venv','node_modules','.git','__pycache__','.opencode')
fail=0
for r in roots:
    for dp,dn,fn in os.walk(r):
        dn[:]=[d for d in dn if d not in skip]
        for f in fn:
            if f.endswith('.py'):
                p=os.path.join(dp,f)
                try: py_compile.compile(p,doraise=True)
                except py_compile.PyCompileError: print("FAIL:",p); fail+=1
print("failures:",fail)
PY
```

**Expected**: `failures: 0` on Python 3.12. Note: on Python 3.10 a small number of files that use
PEP 701 f-strings (backslash inside `{...}`, e.g. `app/tools/recon.py`) will report a false failure -
they are valid on the 3.12 target.

---

## Check 7: Embedding manifest (once implemented, `tasks.md` T029)

```bash
test -f app/core/rag/store/manifest.json && python3 -c "import json;m=json.load(open('app/core/rag/store/manifest.json'));print('dim',m['dimension'],'embedder',m['embedder_name'])"
```

**Expected (post-T029)**: prints the pinned embedder and dimension. Until T029 lands, the file is
absent and RAG uses the legacy path - this check is informational.

---

## Acceptance Criteria (quickstart)

- **AC-1**: Checks 1-6 pass on a clean checkout (Check 6 on Python 3.12).
- **AC-2**: Check 5 reports `CLEAN`.
- **AC-3**: Check 3 returns no importer of a superseded module name.
- **AC-4**: Every marker found in Check 4 names a valid canonical target.

---

## Troubleshooting

- **Duplicate number found (Check 1)**: apply the rename pattern from `tasks.md` T001-T002.
- **Non-ASCII found (Check 5)**: re-run the de-ASCII pass (`tasks.md` T032-T033 approach); preserve
  intentional Unicode as `\uXXXX` escapes.
- **Compile failure on 3.10 (Check 6)**: confirm the file uses a PEP 701 f-string; run on 3.12 before
  treating it as a real failure.
