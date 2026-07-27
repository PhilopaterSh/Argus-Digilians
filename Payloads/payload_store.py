"""payload_store.py - one-record-at-a-time reader for ``Payloads.db``.

Companion to ``build_payload_db.py`` (which ingests the flat ``Payload_data/*.txt``
wordlists into the ``payloads`` table). This module is the *read* side: it hands
back a single payload record per call and remembers where it left off, so an
agent loop can pull "the next path-traversal payload", then "the next one",
without loading a whole wordlist into memory.

Table schema (from build_payload_db.py)::

    payloads(id, payload, vuln_type, context, encoding, source)

Canonical ``vuln_type`` values currently stored: ``traversal``, ``lfi``,
``xss``, ``headers`` (SQLi is supported transparently if later ingested).

The three functions the caller asked for - one per payload type, each
returning ONE record and advancing an internal cursor:

    >>> from Payloads.payload_store import (
    ...     get_traversal_payload, get_lfi_payload, get_xss_payload)
    >>> rec = get_traversal_payload()      # 1st traversal record
    >>> rec.payload
    '../etc/passwd'
    >>> get_traversal_payload().payload    # 2nd traversal record
    '../../etc/passwd'

Each type keeps an independent cursor, so interleaving calls never skip or
collide. By default retrieval is sequential (ordered by ``id``) and *cycles*:
once a type is exhausted the cursor wraps to the first record, so the agent
never runs dry. Set ``cycle=False`` to get ``None`` at the end instead.

Security note
  Only use Argus against targets you own or have written authorisation to
  test. Argus is for authorised security assessment only.
"""

from __future__ import annotations

import random
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

# DB sits next to this file (…/Payloads/Payloads.db), same folder as the
# build script that creates it.
DEFAULT_DB_PATH = Path(__file__).with_name("Payloads.db")

# Friendly aliases -> the canonical vuln_type string stored in the table.
# Mirrors FILE_MAP in build_payload_db.py so callers can pass whichever name
# they think in (``path_traversal``, ``path-traversal``, ``traversal`` …).
_VULN_ALIASES: dict[str, str] = {
    "traversal": "traversal",
    "path_traversal": "traversal",
    "path-traversal": "traversal",
    "dir_traversal": "traversal",
    "lfi": "lfi",
    "local_file_inclusion": "lfi",
    "xss": "xss",
    "cross_site_scripting": "xss",
    "headers": "headers",
    "lowercase-headers": "headers",
    "lowercase_headers": "headers",
    "sqli": "sqli",
    "sql": "sqli",
    "sql-injection": "sqli",
}


def _canonical(vuln_type: str) -> str:
    """Normalise a caller-supplied vuln name to the stored canonical form."""
    key = (vuln_type or "").strip().lower()
    return _VULN_ALIASES.get(key, key)


@dataclass(frozen=True)
class PayloadRecord:
    """One row of the ``payloads`` table."""

    id: int
    payload: str
    vuln_type: str
    context: Optional[str]
    encoding: Optional[str]
    source: Optional[str]

    def __str__(self) -> str:  # so ``str(rec)`` / print gives the raw payload
        return self.payload


class PayloadStore:
    """Stateful, read-only reader over ``Payloads.db``.

    Not a heavy ORM: one shared read-only connection, an independent integer
    cursor per vuln_type, and ``LIMIT 1 OFFSET n`` fetches so memory stays flat
    regardless of table size. Thread-safe (a lock guards cursor advance + fetch).
    """

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        *,
        order: str = "sequential",
        cycle: bool = True,
    ) -> None:
        """
        Args:
            db_path: Path to ``Payloads.db``.
            order: ``"sequential"`` (ordered by id, cursor-driven - the default)
                or ``"random"`` (each call returns a random row of that type;
                cursor/cycle are ignored in this mode).
            cycle: Sequential mode only. When True (default) the cursor wraps to
                the start once a type is exhausted; when False, ``next()``
                returns ``None`` past the end.
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Payload database not found: {self.db_path}")
        if order not in ("sequential", "random"):
            raise ValueError("order must be 'sequential' or 'random'")
        self.order = order
        self.cycle = cycle
        self._cursors: dict[str, int] = {}          # canonical vuln_type -> offset
        self._counts: dict[str, int] = {}           # canonical vuln_type -> cached count
        self._lock = threading.Lock()
        self._conn = self._connect(self.db_path)

    # ---- connection ------------------------------------------------------
    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        """Open a read-only connection, robust to restrictive filesystems.

        Tries a normal ``mode=ro`` open first (correct on a local disk). If the
        environment refuses it - e.g. a network/9p mount with a stale
        ``-journal`` file, which makes even SELECT raise "attempt to write a
        readonly database" - it retries with ``immutable=1``, which tells
        SQLite the file will not change and to skip all locking/journal I/O.
        """
        uri_ro = f"file:{db_path.as_posix()}?mode=ro"
        try:
            conn = sqlite3.connect(uri_ro, uri=True, check_same_thread=False)
            conn.execute("SELECT 1 FROM payloads LIMIT 1")  # probe for hot-journal errors
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.OperationalError:
            uri_imm = f"file:{db_path.as_posix()}?immutable=1"
            conn = sqlite3.connect(uri_imm, uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    # ---- counts ----------------------------------------------------------
    def count(self, vuln_type: str) -> int:
        """Total records stored for ``vuln_type`` (cached after first lookup)."""
        vt = _canonical(vuln_type)
        if vt not in self._counts:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM payloads WHERE vuln_type = ?", (vt,)
            ).fetchone()
            self._counts[vt] = int(row[0]) if row else 0
        return self._counts[vt]

    def available_types(self) -> list[str]:
        """Distinct canonical vuln_types actually present in the DB."""
        rows = self._conn.execute(
            "SELECT DISTINCT vuln_type FROM payloads ORDER BY vuln_type"
        ).fetchall()
        return [r[0] for r in rows]

    # ---- core retrieval --------------------------------------------------
    def _row_to_record(self, row: sqlite3.Row) -> PayloadRecord:
        return PayloadRecord(
            id=row["id"],
            payload=row["payload"],
            vuln_type=row["vuln_type"],
            context=row["context"],
            encoding=row["encoding"],
            source=row["source"],
        )

    def next(self, vuln_type: str) -> Optional[PayloadRecord]:
        """Return the next single record of ``vuln_type`` (or None).

        Sequential mode: returns the record at the type's current cursor and
        advances by one; wraps to the start when ``cycle`` is True, else returns
        None once exhausted. Random mode: returns a random record each call.

        Returns None only when the type has zero records, or when the cursor is
        past the end and ``cycle`` is False.
        """
        vt = _canonical(vuln_type)
        total = self.count(vt)
        if total == 0:
            return None

        with self._lock:
            if self.order == "random":
                offset = random.randrange(total)
            else:
                offset = self._cursors.get(vt, 0)
                if offset >= total:
                    if not self.cycle:
                        return None
                    offset = 0
                self._cursors[vt] = offset + 1

            row = self._conn.execute(
                "SELECT id, payload, vuln_type, context, encoding, source "
                "FROM payloads WHERE vuln_type = ? ORDER BY id LIMIT 1 OFFSET ?",
                (vt, offset),
            ).fetchone()

        return self._row_to_record(row) if row else None

    # ---- convenience: the three per-type functions -----------------------
    def next_traversal(self) -> Optional[PayloadRecord]:
        """Next path-traversal record (one at a time)."""
        return self.next("traversal")

    def next_lfi(self) -> Optional[PayloadRecord]:
        """Next Local-File-Inclusion record (one at a time)."""
        return self.next("lfi")

    def next_xss(self) -> Optional[PayloadRecord]:
        """Next XSS record (one at a time)."""
        return self.next("xss")

    # ---- cursor management ----------------------------------------------
    def reset(self, vuln_type: Optional[str] = None) -> None:
        """Rewind one type's cursor to the start, or all cursors when None."""
        with self._lock:
            if vuln_type is None:
                self._cursors.clear()
            else:
                self._cursors.pop(_canonical(vuln_type), None)

    def remaining(self, vuln_type: str) -> int:
        """Records left before the cursor wraps/exhausts (sequential mode)."""
        vt = _canonical(vuln_type)
        return max(0, self.count(vt) - self._cursors.get(vt, 0))

    def iter_type(self, vuln_type: str) -> Iterator[PayloadRecord]:
        """Yield every record of a type exactly once (ignores cycle; stops at
        end). A convenience generator on top of the same OFFSET walk."""
        vt = _canonical(vuln_type)
        total = self.count(vt)
        for offset in range(total):
            row = self._conn.execute(
                "SELECT id, payload, vuln_type, context, encoding, source "
                "FROM payloads WHERE vuln_type = ? ORDER BY id LIMIT 1 OFFSET ?",
                (vt, offset),
            ).fetchone()
            if row:
                yield self._row_to_record(row)

    # ---- lifecycle -------------------------------------------------------
    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    def __enter__(self) -> "PayloadStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Module-level default store + the three standalone functions
# ---------------------------------------------------------------------------
_default_store: Optional[PayloadStore] = None
_default_lock = threading.Lock()


def get_store() -> PayloadStore:
    """Return the process-wide default store (lazily opened on first use)."""
    global _default_store
    if _default_store is None:
        with _default_lock:
            if _default_store is None:
                _default_store = PayloadStore()
    return _default_store


def get_traversal_payload() -> Optional[PayloadRecord]:
    """Retrieve ONE path-traversal payload record, advancing the cursor."""
    return get_store().next_traversal()


def get_lfi_payload() -> Optional[PayloadRecord]:
    """Retrieve ONE Local-File-Inclusion payload record, advancing the cursor."""
    return get_store().next_lfi()


def get_xss_payload() -> Optional[PayloadRecord]:
    """Retrieve ONE XSS payload record, advancing the cursor."""
    return get_store().next_xss()


def get_payload(vuln_type: str) -> Optional[PayloadRecord]:
    """Retrieve ONE record of any ``vuln_type`` (e.g. 'headers', 'sqli')."""
    return get_store().next(vuln_type)


def reset(vuln_type: Optional[str] = None) -> None:
    """Rewind the default store's cursor(s)."""
    get_store().reset(vuln_type)


# ---------------------------------------------------------------------------
# CLI smoke test:  python payload_store.py [vuln_type] [n]
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover
    import sys

    vt = sys.argv[1] if len(sys.argv) > 1 else "traversal"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    store = PayloadStore()
    print(f"[i] DB: {store.db_path}")
    print(f"[i] available types: {store.available_types()}")
    print(f"[i] count({vt}) = {store.count(vt)}")
    print(f"[i] first {n} '{vt}' records (one at a time):")
    for _ in range(n):
        rec = store.next(vt)
        if rec is None:
            print("    <none>")
            break
        print(f"    id={rec.id:<5} enc={rec.encoding or '-':<12} {rec.payload[:70]}")
    store.close()
