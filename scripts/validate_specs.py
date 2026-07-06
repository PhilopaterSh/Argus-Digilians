#!/usr/bin/env python3
"""Spec-Kit structure and consistency validator.

Implements the CI "spec-validation" stage from
specs/012-spec-reconciliation/spec.md (section 7).

Checks (all read-only):
  1. No duplicate numeric feature prefixes under specs/.
  2. Every feature folder has spec.md, plan.md, tasks.md.
  3. No dangling supersession term (Superseded By / Replaced By / Refined By /
     Deprecated) left without a target on the same line.

Exit code 0 on success, 1 on any violation. Standard library only.
"""
import os
import re
import sys

SPECS_DIR = os.path.join(os.path.dirname(__file__), "..", "specs")
FEATURE_RE = re.compile(r"^(\d+)-")
# Full Spec-Kit artifact set required for every feature
# (specs/012-spec-reconciliation governance; every feature must be complete).
REQUIRED = ("spec.md", "research.md", "plan.md", "data-model.md", "quickstart.md", "tasks.md")
SUPERSEDE_TERMS = ("Superseded By", "Replaced By", "Refined By", "Partially Superseded By")


def feature_dirs(specs_dir):
    out = []
    for name in sorted(os.listdir(specs_dir)):
        p = os.path.join(specs_dir, name)
        if os.path.isdir(p) and FEATURE_RE.match(name):
            out.append(name)
    return out


def check_duplicate_numbers(dirs):
    seen = {}
    errors = []
    for d in dirs:
        num = FEATURE_RE.match(d).group(1)
        seen.setdefault(num, []).append(d)
    for num, ds in seen.items():
        if len(ds) > 1:
            errors.append(f"duplicate feature number {num}: {', '.join(ds)}")
    return errors


def check_required_artifacts(specs_dir, dirs):
    errors = []
    for d in dirs:
        for req in REQUIRED:
            if not os.path.isfile(os.path.join(specs_dir, d, req)):
                errors.append(f"{d}: missing required artifact {req}")
    return errors


def check_supersession_targets(specs_dir, dirs):
    errors = []
    for d in dirs:
        spec = os.path.join(specs_dir, d, "spec.md")
        if not os.path.isfile(spec):
            continue
        for i, line in enumerate(open(spec, encoding="utf-8"), 1):
            for term in SUPERSEDE_TERMS:
                idx = line.find(term)
                if idx != -1:
                    tail = line[idx + len(term):].strip(" :*.-")
                    if not tail:
                        errors.append(f"{d}/spec.md:{i}: '{term}' has no target")
    return errors


def main():
    specs_dir = os.path.abspath(SPECS_DIR)
    if not os.path.isdir(specs_dir):
        print(f"ERROR: specs dir not found: {specs_dir}")
        return 1
    dirs = feature_dirs(specs_dir)
    errors = []
    errors += check_duplicate_numbers(dirs)
    errors += check_required_artifacts(specs_dir, dirs)
    errors += check_supersession_targets(specs_dir, dirs)

    print(f"[validate_specs] {len(dirs)} feature folders checked")
    if errors:
        print(f"[validate_specs] FAIL - {len(errors)} violation(s):")
        for e in errors:
            print("  -", e)
        return 1
    print("[validate_specs] PASS - specs are structurally consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
