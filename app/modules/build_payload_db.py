#!/usr/bin/env python3
"""
build_payload_db.py - Ingest flat payload .txt files into a searchable SQLite DB.
Layout expected:
    payloads/sqli.txt
    payloads/xss.txt
    payloads/lfi.txt
    payloads/path_traversal.txt
    payloads/lowercase-headers.txt
Usage:
    python3 build_payload_db.py ./payloads ./payloads.db
"""
import sqlite3, sys, re
from pathlib import Path

# filename stem -> canonical vuln_type
FILE_MAP = {
    "sqli": "sqli", "sql": "sqli", "sql-injection": "sqli",
    "xss": "xss", "xss-payload-list": "xss",
    "lfi": "lfi",
    # path traversal kept as its own class (distinct from lfi), matches your file names
    "path_traversal": "traversal", "path-traversal": "traversal", "traversal": "traversal",
    # HTTP header wordlist (fuzzing / smuggling / normalization) - not an injection class
    "lowercase-headers": "headers", "lowercase_headers": "headers", "headers": "headers",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS payloads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    payload     TEXT NOT NULL,
    vuln_type   TEXT NOT NULL,
    context     TEXT,
    encoding    TEXT,
    source      TEXT,
    UNIQUE(payload, vuln_type)
);
CREATE INDEX IF NOT EXISTS idx_vuln    ON payloads(vuln_type);
CREATE INDEX IF NOT EXISTS idx_context ON payloads(vuln_type, context);
"""

def infer_context(p, vuln):
    """Coarse, honest heuristics - refine later if needed."""
    if vuln == "xss":
        if re.search(r'^\s*["\']?\s*on\w+\s*=', p) or p.strip().startswith(('"', "'")):
            return "html_attribute"
        if "javascript:" in p.lower():
            return "uri"
        if "<" in p:
            return "html_body"
        return "js_string"
    if vuln in ("lfi", "traversal"):
        return "windows" if ("\\" in p or "boot.ini" in p.lower() or "win.ini" in p.lower()) else "linux"
    if vuln == "headers":
        return None
    return None

def infer_encoding(p):
    lp = p.lower()
    if "%252e" in lp or "%255c" in lp:
        return "double_url"
    if "%2e" in lp or "%2f" in lp or "%5c" in lp:
        return "url"
    if "&#" in p:
        return "html_entity"
    return "none"

def clean_lines(path):
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.rstrip("\n").rstrip("\r")
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        yield line

def main(src_dir, db_path):
    src, db = Path(src_dir), sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    total = 0
    for f in sorted(src.glob("*.txt")):
        vuln = FILE_MAP.get(f.stem.lower())
        if not vuln:
            print("[!] Skipping unmapped file: " + f.name)
            continue
        rows = [
            (p, vuln, infer_context(p, vuln), infer_encoding(p), f.name)
            for p in clean_lines(f)
        ]
        cur = db.executemany(
            "INSERT OR IGNORE INTO payloads "
            "(payload, vuln_type, context, encoding, source) VALUES (?,?,?,?,?)",
            rows,
        )
        db.commit()
        print("[+] {}: {} read, {} new -> {}".format(f.name, len(rows), cur.rowcount, vuln))
        total += len(rows)
    for vt, n in db.execute("SELECT vuln_type, COUNT(*) FROM payloads GROUP BY vuln_type ORDER BY vuln_type"):
        print("    {}: {} stored".format(vt, n))
    db.close()
    print("[done] DB: " + db_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 build_payload_db.py <payloads_dir> <output.db>")
    main(sys.argv[1], sys.argv[2])
