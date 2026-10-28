"""Google-style docstring compliance gate (specs/016-docstring-enforcement).

Checks that function definitions have a docstring whose Args/Returns/Raises
sections actually match the function's real signature and body - not just
that *a* docstring exists. Two modes:

    --diff <base_ref>   Only check functions added/modified vs base_ref.
                         This is the CI-blocking mode (stage 1): new code
                         must be compliant, old code is not retroactively
                         broken by this gate.
    --all                Check every function in the scanned paths and
                         report full coverage. Informational only (stage 1);
                         becomes blocking per-directory as backfill lands
                         (see specs/checklist.md CHK05x series).

Exit code is 0 (pass) or 1 (violations found), so it drops straight into
CI or a pre-commit hook.
"""
import argparse
import ast
import subprocess
import sys
from pathlib import Path

EXCLUDE_DIRS = {
    "Argus_venv", "node_modules", "archive", ".opencode", "__pycache__",
    ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache", "workspace", ".specify",
}

# Functions this trivial don't need a full Args/Returns/Raises breakdown -
# a one-line summary docstring is sufficient. Keeps the gate from demanding
# ceremony for e.g. `def __repr__(self): return self.name`.
TRIVIAL_BODY_MAX_STATEMENTS = 1


def iter_py_files(paths):
    """Yield every .py file under the given paths, skipping excluded dirs.

    Args:
        paths (list[str]): Root files or directories to walk.

    Yields:
        pathlib.Path: Each discovered ``.py`` file.
    """
    for raw in paths:
        p = Path(raw)
        if p.is_file() and p.suffix == ".py":
            yield p
            continue
        for dirpath, dirnames, filenames in __import__("os").walk(p):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in filenames:
                if fn.endswith(".py"):
                    yield Path(dirpath) / fn


def changed_line_ranges(base_ref):
    """Return {file: set(changed_line_numbers)} from `git diff base_ref...HEAD`.

    Args:
        base_ref (str): Git ref (branch, tag, or commit) to diff against.

    Returns:
        dict[str, set[int]]: Changed line numbers per file path (as they
        appear in the diff's "to" side), restricted to ``.py`` files.
    """
    out = subprocess.run(
        ["git", "diff", "--unified=0", f"{base_ref}...HEAD", "--", "*.py"],
        capture_output=True, check=True,
    ).stdout.decode("utf-8", errors="replace")
    result = {}
    current_file = None
    for line in out.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            result[current_file] = set()
        elif line.startswith("@@") and current_file:
            # @@ -a,b +c,d @@  -> new-side start line c, length d (default 1)
            hunk = line.split("@@")[1].strip()
            new_part = hunk.split(" ")[1]
            start = int(new_part.split(",")[0].lstrip("+"))
            length = int(new_part.split(",")[1]) if "," in new_part else 1
            result[current_file].update(range(start, start + max(length, 1)))
    return result


def walk_own_body(func):
    """Walk a function's descendants without crossing into nested defs.

    Plain ``ast.walk`` would also yield nodes belonging to any nested
    function/lambda, so a `return` inside a nested helper would incorrectly
    count as the outer function's own return.

    Args:
        func (ast.FunctionDef | ast.AsyncFunctionDef): The function node.

    Yields:
        ast.AST: Each descendant node that belongs to this function's own
        body, not to a nested function/lambda's body.
    """
    stack = list(func.body)
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                stack.append(child)


def required_sections(func: ast.FunctionDef | ast.AsyncFunctionDef):
    """Determine which Google docstring sections this function needs.

    Args:
        func (ast.FunctionDef | ast.AsyncFunctionDef): The function node.

    Returns:
        set[str]: Subset of {"Args", "Returns", "Raises"} that a compliant
        docstring for this function must contain.
    """
    needed = set()
    params = [a for a in func.args.args if a.arg not in ("self", "cls")]
    if params or func.args.vararg or func.args.kwarg or func.args.kwonlyargs:
        needed.add("Args")
    own_body = list(walk_own_body(func))
    has_return_value = any(isinstance(n, ast.Return) and n.value is not None for n in own_body)
    has_return_annotation = func.returns is not None and getattr(func.returns, "id", None) != "None"
    if has_return_value or has_return_annotation:
        needed.add("Returns")
    if any(isinstance(n, ast.Raise) for n in own_body):
        needed.add("Raises")
    return needed


def check_function(func, filename):
    """Validate one function's docstring against its real signature/body.

    Args:
        func (ast.FunctionDef | ast.AsyncFunctionDef): The function to check.
        filename (str): Path used in reported violation messages.

    Returns:
        list[str]: Human-readable violation messages; empty if compliant.
    """
    body_len = len(func.body) - (1 if ast.get_docstring(func) else 0)
    doc = ast.get_docstring(func)
    violations = []
    if not doc:
        violations.append(f"{filename}:{func.lineno} `{func.name}` - missing docstring")
        return violations
    for section in required_sections(func):
        if body_len <= TRIVIAL_BODY_MAX_STATEMENTS:
            continue  # one-line summary is enough for trivial functions
        if f"{section}:" not in doc:
            violations.append(
                f"{filename}:{func.lineno} `{func.name}` - docstring missing `{section}:` section"
            )
    return violations


def main():
    """CLI entry point: parse args, scan, print violations, set exit code.

    Returns:
        int: 1 if violations were found and this run was in a blocking
        mode (`--diff <ref>`, or the default full-scan invocation without
        `--all`); 0 otherwise (no violations, or `--all` was passed for
        an informational-only report).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["app", "scripts"])
    parser.add_argument("--diff", metavar="BASE_REF", help="Only check lines changed vs BASE_REF")
    parser.add_argument("--all", action="store_true", help="Check every function (coverage report)")
    args = parser.parse_args()

    changed = changed_line_ranges(args.diff) if args.diff else None
    all_violations = []
    scanned = 0

    for path in iter_py_files(args.paths):
        key = str(path).replace("\\", "/")
        if changed is not None and key not in changed:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if changed is not None and not (changed.get(key, set()) & set(range(node.lineno, node.end_lineno + 1))):
                continue
            scanned += 1
            all_violations.extend(check_function(node, key))

    if args.all:
        print(f"Scanned {scanned} functions.")
    for v in all_violations:
        print(v)

    if all_violations and (args.diff or args.all is False):
        print(f"\n{len(all_violations)} docstring violation(s) found.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
