"""No-duplication compliance gate (Constitution IX, specs/017-no-duplication-policy).

Detects two classes of duplication across the repository:

    1. Byte-identical files (e.g. two requirements.txt with the same
       content copy-pasted instead of one canonical file).
    2. Structurally-identical Python functions defined independently in
       more than one file (same logic, hand-copied instead of shared).

Modes:
    --diff <base_ref>   Only flag NEW duplication introduced since base_ref
                         (a new file/function that duplicates something that
                         already existed). CI-blocking mode (stage 1) - does
                         not retroactively fail on the existing, already
                         tracked duplication backlog (see specs/checklist.md).
    --all                Report every duplicate group found. Informational.

Exit code 0 (pass) or 1 (new violations found), same convention as
scripts/check_docstrings.py.
"""
import argparse
import ast
import hashlib
import os
import subprocess
import sys
from pathlib import Path

EXCLUDE_DIRS = {
    "Argus_venv", "node_modules", "archive", ".opencode", "__pycache__",
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".specify",
}

# Files under these sizes are exempt from exact-file-duplication checks -
# e.g. `__init__.py` empty markers or `.gitkeep` are *supposed* to be
# identical everywhere and are not meaningful duplication.
MIN_FILE_SIZE_BYTES = 20

# Functions with a body this short (statement count, docstring excluded)
# are exempt from function-duplication checks - trivial one-liners like
# `def __repr__(self): return self.name` will legitimately look identical
# across unrelated classes.
TRIVIAL_BODY_MAX_STATEMENTS = 1


def iter_files(paths, suffix=None):
    """Yield every file under the given paths, skipping excluded dirs.

    Args:
        paths (list[str]): Root files or directories to walk.
        suffix (str | None): If given, only yield files with this suffix.

    Yields:
        pathlib.Path: Each discovered file.
    """
    for raw in paths:
        p = Path(raw)
        if p.is_file():
            if suffix is None or p.suffix == suffix:
                yield p
            continue
        for dirpath, dirnames, filenames in os.walk(p):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                if suffix is None or fn.endswith(suffix):
                    yield Path(dirpath) / fn


def find_duplicate_files(paths):
    """Group files by content hash to find byte-identical duplicates.

    Args:
        paths (list[str]): Root files or directories to scan.

    Returns:
        dict[str, list[str]]: Maps a content hash to the list of file
        paths sharing that exact content, restricted to groups with more
        than one file.
    """
    by_hash = {}
    for path in iter_files(paths):
        if path.name == "__init__.py":
            # Package-marker files are expected to be identical (often a
            # single boilerplate comment or nothing at all) across an
            # entire package tree - that's convention, not duplication.
            continue
        try:
            data = path.read_bytes()
        except (IsADirectoryError, PermissionError, OSError):
            continue
        if len(data) < MIN_FILE_SIZE_BYTES:
            continue
        digest = hashlib.sha256(data).hexdigest()
        by_hash.setdefault(digest, []).append(str(path).replace("\\", "/"))
    return {h: files for h, files in by_hash.items() if len(files) > 1}


def normalized_function_source(func):
    """Render a function body as a docstring-stripped, whitespace-canonical string.

    Args:
        func (ast.FunctionDef | ast.AsyncFunctionDef): The function to normalize.

    Returns:
        str: `ast.unparse` output of the function's body with any leading
        docstring expression removed, so formatting/whitespace/comment
        differences don't mask identical logic, and differing prose
        docstrings don't mask (or falsely flag) identical code.
    """
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body:
        return ""
    return "\n".join(ast.unparse(stmt) for stmt in body)


def find_duplicate_functions(paths):
    """Group functions by normalized body to find structurally-identical logic.

    Args:
        paths (list[str]): Root files or directories to scan for `.py` files.

    Returns:
        dict[str, list[str]]: Maps a normalized-body hash to a list of
        "file:line `func_name`" locations sharing that exact normalized
        body, restricted to groups spanning more than one file (same-file
        helper overloads are not flagged) and to non-trivial bodies.
    """
    by_hash = {}
    for path in iter_files(paths, suffix=".py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body_len = len(node.body) - (1 if ast.get_docstring(node) else 0)
            if body_len <= TRIVIAL_BODY_MAX_STATEMENTS:
                continue
            normalized = normalized_function_source(node)
            if not normalized:
                continue
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            key = str(path).replace("\\", "/")
            by_hash.setdefault(digest, []).append(f"{key}:{node.lineno} `{node.name}`")

    result = {}
    for digest, locations in by_hash.items():
        files_involved = {loc.split(":")[0] for loc in locations}
        if len(files_involved) > 1:
            result[digest] = locations
    return result


def changed_files(base_ref):
    """Return the set of files added or modified vs base_ref.

    Args:
        base_ref (str): Git ref to diff against.

    Returns:
        set[str]: File paths (as they appear on the diff's "to" side).
    """
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def main():
    """CLI entry point: parse args, scan, print duplicate groups, set exit code.

    Returns:
        int: 1 if duplication violations were found and this run was in a
        blocking mode (`--diff <ref>`, or the default full-scan invocation
        without `--all`); 0 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--diff", metavar="BASE_REF", help="Only flag NEW duplication vs BASE_REF")
    parser.add_argument("--all", action="store_true", help="Report every duplicate group (informational)")
    args = parser.parse_args()

    dup_files = find_duplicate_files(args.paths)
    dup_funcs = find_duplicate_functions(args.paths)

    changed = changed_files(args.diff) if args.diff else None
    violations = []

    for _digest, files in dup_files.items():
        if changed is not None and not (set(files) & changed):
            continue
        violations.append(f"Duplicate file content ({len(files)} files): {', '.join(files)}")

    for _digest, locations in dup_funcs.items():
        touched_files = {loc.split(":")[0] for loc in locations}
        if changed is not None and not (touched_files & changed):
            continue
        violations.append(f"Duplicate function logic ({len(locations)} locations): {', '.join(locations)}")

    if args.all:
        print(f"{len(dup_files)} duplicate-file group(s), {len(dup_funcs)} duplicate-function group(s) total.")
    for v in violations:
        print(v)

    if violations and (args.diff or not args.all):
        print(f"\n{len(violations)} duplication violation(s) found.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
