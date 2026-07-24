#!/usr/bin/env python3
"""Spec-Kit structure and consistency validator.

Implements the CI "spec-validation" stage from
specs/012-spec-reconciliation/spec.md (section 7).

Checks (all read-only):
  1. No duplicate numeric feature prefixes under specs/.
  2. Every feature folder has the artifact set its own lifecycle status
     requires (see STATUS_TIER below) - not a blanket six-file template.
  3. No dangling supersession term (Superseded By / Replaced By / Refined By /
     Deprecated) left without a target on the same line.

Exit code 0 on success, 1 on any violation. Standard library only.
"""
import os
import re
import sys

SPECS_DIR = os.path.join(os.path.dirname(__file__), "..", "specs")
FEATURE_RE = re.compile(r"^(\d+)-")
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*(.+)$", re.MULTILINE)
APPLICABILITY_RE = re.compile(r"^-\s*(\S+):\s*N/A\s*\u2014\s*\S.*$", re.MULTILINE)

# A feature's own **Status** line (in its spec.md) determines which artifacts
# are actually meaningful to require - not every feature has reached (or
# will reach) a stage where a data model or an end-user quickstart exists.
# CORE artifacts are the auditable record of "what was this and how was it
# built"; CONDITIONAL artifacts may be genuinely not applicable, in which
# case spec.md must say so explicitly (see APPLICABILITY_RE) rather than
# silently omitting them.
MINIMAL_STATUSES = ("Draft", "Fully Superseded")
CORE_STATUSES = ("Proposed", "Implemented", "Active")
CORE = ("spec.md", "research.md", "plan.md", "tasks.md")
CONDITIONAL = ("data-model.md", "quickstart.md")
SUPERSEDE_TERMS = ("Superseded By", "Replaced By", "Refined By", "Partially Superseded By")


def feature_dirs(specs_dir):
    """List every numbered feature folder directly under specs_dir.

    Args:
        specs_dir (str): Path to the repository's `specs/` directory.

    Returns:
        list[str]: Sorted directory names matching FEATURE_RE (a leading
        digit sequence followed by `-`), e.g. "027-merge-branches".
    """
    out = []
    for name in sorted(os.listdir(specs_dir)):
        p = os.path.join(specs_dir, name)
        if os.path.isdir(p) and FEATURE_RE.match(name):
            out.append(name)
    return out


def check_duplicate_numbers(dirs):
    """Find feature folders that share the same leading number prefix.

    Args:
        dirs (list[str]): Feature folder names, as returned by feature_dirs.

    Returns:
        list[str]: One error message per duplicated number, naming every
        folder sharing that number; empty if every number is unique.
    """
    seen = {}
    errors = []
    for d in dirs:
        num = FEATURE_RE.match(d).group(1)
        seen.setdefault(num, []).append(d)
    for num, ds in seen.items():
        if len(ds) > 1:
            errors.append(f"duplicate feature number {num}: {', '.join(ds)}")
    return errors


def _read_spec_text(specs_dir, d):
    """Read a feature folder's spec.md, if it exists.

    Args:
        specs_dir (str): Path to the repository's `specs/` directory.
        d (str): Feature folder name.

    Returns:
        str | None: The full text of `<specs_dir>/<d>/spec.md`, or `None`
        if that file doesn't exist.
    """
    spec_path = os.path.join(specs_dir, d, "spec.md")
    if not os.path.isfile(spec_path):
        return None
    with open(spec_path, encoding="utf-8") as f:
        return f.read()


def _status_tier(spec_text, d, errors):
    """Determine which artifact tier a feature's spec.md status implies.

    Appends a human-readable message to `errors` (in place) if spec_text
    is missing a recognizable `**Status**: ...` header or has a status
    this validator doesn't recognize.

    Args:
        spec_text (str | None): The feature's spec.md content, or `None`
            if the file doesn't exist.
        d (str): Feature folder name, used in any appended error message.
        errors (list[str]): Error-message accumulator, mutated in place.

    Returns:
        tuple[str, ...]: The artifact filenames this feature must have -
        `("spec.md",)` for MINIMAL_STATUSES, `CORE` for CORE_STATUSES or
        any unrecognized/missing status (the safer, stricter default).
    """
    if spec_text is None:
        return CORE  # no spec.md at all - fall through to check_required_artifacts's own report
    m = STATUS_RE.search(spec_text)
    if not m:
        errors.append(f"{d}/spec.md: no '**Status**: ...' header found - cannot determine required artifacts")
        return CORE
    status_line = m.group(1)
    if any(status_line.startswith(s) for s in MINIMAL_STATUSES):
        return ("spec.md",)
    if any(status_line.startswith(s) for s in CORE_STATUSES):
        return CORE
    errors.append(f"{d}/spec.md: unrecognized status '{status_line.strip()}' - cannot determine required artifacts")
    return CORE


def check_required_artifacts(specs_dir, dirs):
    """Verify each feature folder has the artifacts its status tier requires.

    For CORE-tier features, conditional artifacts (data-model.md,
    quickstart.md) may be omitted only if spec.md explicitly declares them
    N/A with a reason under an "## Artifact applicability" section
    (APPLICABILITY_RE).

    Args:
        specs_dir (str): Path to the repository's `specs/` directory.
        dirs (list[str]): Feature folder names to check.

    Returns:
        list[str]: One error message per missing required or
        undeclared-conditional artifact; empty if every folder satisfies
        its tier's requirements.
    """
    errors = []
    for d in dirs:
        spec_text = _read_spec_text(specs_dir, d)
        tier = _status_tier(spec_text, d, errors)
        for req in tier:
            if not os.path.isfile(os.path.join(specs_dir, d, req)):
                errors.append(f"{d}: missing required artifact {req}")
        if tier is CORE:
            declared_na = set(APPLICABILITY_RE.findall(spec_text)) if spec_text else set()
            for cond in CONDITIONAL:
                exists = os.path.isfile(os.path.join(specs_dir, d, cond))
                if not exists and cond not in declared_na:
                    errors.append(
                        f"{d}: missing conditional artifact {cond} (add the file, or declare it "
                        f"N/A with a reason under spec.md's '## Artifact applicability' section)"
                    )
    return errors


def check_supersession_targets(specs_dir, dirs):
    """Find supersession markers (e.g. "Superseded By") left without a target.

    Args:
        specs_dir (str): Path to the repository's `specs/` directory.
        dirs (list[str]): Feature folder names to scan.

    Returns:
        list[str]: One error message per line where a SUPERSEDE_TERMS
        marker has no non-empty text after it; empty if every marker
        names a target.
    """
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
    """CLI entry point: run all three structural checks and print a pass/fail summary.

    Returns:
        int: 1 if the specs directory is missing or any check reported a
        violation, 0 if all feature folders are structurally consistent.
    """
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
