#!/usr/bin/env python3
"""ASCII / English-only validator for first-party code.

Implements the CI "doc-validation" (ASCII-safe) stage from
specs/012-spec-reconciliation/spec.md (section 7) and enforces
Constitution principle VI (ASCII-safe console/log output, no mixed-language files).

Scans app/, scripts/, tests/ plus config/config.yaml for non-ASCII bytes in
code/config files. Exit code 0 if clean, 1 if any non-ASCII byte is found.
Standard library only.
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
ROOTS = ("app", "scripts", "tests")
EXTRA_FILES = ("config/config.yaml",)
SKIP_DIRS = ("Argus_venv", "node_modules", ".git", "__pycache__", ".opencode", "archive")
EXTS = (".py", ".bat", ".ps1", ".sh", ".yaml", ".yml", ".cfg", ".ini", ".toml")


def scan_file(path):
    with open(path, "rb") as f:
        data = f.read()
    return [i for i, b in enumerate(data) if b >= 128]


def iter_files(root):
    for base in ROOTS:
        base_path = os.path.join(root, base)
        if not os.path.isdir(base_path):
            continue
        for dp, dn, fn in os.walk(base_path):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fn:
                if f.endswith(EXTS):
                    yield os.path.join(dp, f)
    for extra in EXTRA_FILES:
        p = os.path.join(root, extra)
        if os.path.isfile(p):
            yield p


def main():
    root = os.path.abspath(ROOT)
    dirty = []
    total = 0
    for path in iter_files(root):
        total += 1
        bad = scan_file(path)
        if bad:
            dirty.append((os.path.relpath(path, root), len(bad)))

    print(f"[validate_ascii] {total} files scanned")
    if dirty:
        print(f"[validate_ascii] FAIL - {len(dirty)} file(s) contain non-ASCII bytes:")
        for p, n in dirty:
            print(f"  - {p} ({n} non-ASCII bytes)")
        print("  Fix: replace symbols/emoji with ASCII; keep intentional Unicode "
              "test data as \\uXXXX escapes.")
        return 1
    print("[validate_ascii] PASS - first-party code is ASCII/English-only")
    return 0


if __name__ == "__main__":
    sys.exit(main())
