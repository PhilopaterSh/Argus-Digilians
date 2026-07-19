import sqlite3
import json
import os
import logging
import shutil
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Any

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = os.path.join("data", "argus_intelligence.db")
_ROOT_DB_PATH = "argus_intelligence.db"
_SCHEMA_VERSION = 3
_PRIORITY_TARGET_BAD_SUBSTRINGS = ("error", "---", "code ", "suggestion:", "not found", "command")


class ArgusMemory:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        if self.db_path != ":memory:":
            self._migrate_from_root()
            if not self._db_ok():
                self._reset_corrupt_db()
        self._init_db()
        if self.db_path != ":memory:":
            self._verify_integrity()

    # ------------------------------------------------------------------
    # Corruption detection and recovery
    # ------------------------------------------------------------------
    def _db_ok(self) -> bool:
        """True if the DB file is a valid SQLite database (or doesn't exist yet).
        Always closes the probe connection so the file is not left locked."""
        if not os.path.exists(self.db_path):
            return True
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            return True
        except sqlite3.DatabaseError:
            return False
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    def _reset_corrupt_db(self) -> None:
        """Handle a malformed SQLite file: keep the bad file as *.corrupt
        (for inspection) and clear any side files so a clean DB can be built."""
        for suffix in ("", "-journal", "-wal", "-shm"):
            p = self.db_path + suffix
            try:
                if not os.path.exists(p):
                    continue
                if suffix == "":
                    try:
                        os.replace(p, p + ".corrupt")
                        continue
                    except OSError:
                        pass
                os.remove(p)
            except OSError:
                pass
        logger.warning(
            "Corrupt database detected -> rebuilt a fresh %s (old file saved as %s.corrupt)",
            self.db_path, self.db_path,
        )

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------
    @contextmanager
    def _get_conn(self) -> Any:
        # 10s was too tight for the actual concurrency pattern: the LangGraph
        # agent subprocess (each node re-instantiates ArgusMemory, so this
        # opens/closes several connections per run) writes to this same file
        # while the Streamlit GUI's status bar polls it on every st.fragment
        # refresh. A single "database is locked" hit on the one add_finding()
        # call per recon pass silently drops that write with no retry - see
        # CHANGELOG.md 2026-07-08 Blackboard-write investigation.
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Migration from root db
    # ------------------------------------------------------------------
    def _migrate_from_root(self) -> None:
        if not os.path.exists(_ROOT_DB_PATH):
            return
        if self.db_path == _ROOT_DB_PATH:
            return
        target_exists = os.path.exists(self.db_path)
        try:
            src_conn = sqlite3.connect(_ROOT_DB_PATH)
            dst_conn = sqlite3.connect(self.db_path)
            dst_conn.execute("PRAGMA journal_mode=WAL")
            dst_conn.execute("PRAGMA foreign_keys=ON")
            tables = [
                t[0]
                for t in src_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                if t[0] != "schema_version"
            ]
            if not target_exists:
                src_conn.backup(dst_conn)
                logger.info("Migrated root DB to %s (%d tables)", self.db_path, len(tables))
            else:
                for table in tables:
                    rows = src_conn.execute(f"SELECT * FROM [{table}]").fetchall()
                    if rows:
                        col_names = [d[0] for d in src_conn.execute(f"PRAGMA table_info([{table}])").fetchall()]
                        placeholders = ", ".join("?" for _ in col_names)
                        cols = ", ".join(f"[{c}]" for c in col_names)
                        for row in rows:
                            try:
                                dst_conn.execute(
                                    f"INSERT OR IGNORE INTO [{table}] ({cols}) VALUES ({placeholders})",
                                    row,
                                )
                            except Exception:
                                pass
                    dst_conn.commit()
                logger.info("Merged %d tables from root DB", len(tables))
            src_conn.close()
            dst_conn.close()
            os.remove(_ROOT_DB_PATH)
            logger.info("Root DB removed after migration")
        except Exception as e:
            logger.warning("Root DB migration failed: %s", e)

    # ------------------------------------------------------------------
    # Integrity check
    # ------------------------------------------------------------------
    def _verify_integrity(self) -> None:
        """Verify integrity."""
        try:
            with self._get_conn() as conn:
                row = conn.execute("PRAGMA integrity_check").fetchone()
                if row and row[0] != "ok":
                    logger.warning("Database integrity issue: %s", row[0])
        except Exception as e:
            logger.warning("Could not verify integrity: %s", e)

    # ------------------------------------------------------------------
    # Schema versioning
    # ------------------------------------------------------------------
    def _get_schema_version(self) -> int:
        """Get schema version."""
        try:
            with self._get_conn() as conn:
                row = conn.execute("PRAGMA user_version").fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def _set_schema_version(self, version: int) -> None:
        """Set schema version."""
        try:
            with self._get_conn() as conn:
                conn.execute(f"PRAGMA user_version = {version}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Database initialization
    # ------------------------------------------------------------------
    def _init_db(self) -> None:
        """Init db."""
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS targets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        domain TEXT UNIQUE,
                        parent_domain TEXT,
                        status TEXT DEFAULT 'discovered',
                        priority INTEGER DEFAULT 0,
                        last_seen DATETIME
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS findings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_id INTEGER,
                        tool_name TEXT,
                        data_type TEXT,
                        raw_data TEXT,
                        summary TEXT,
                        timestamp DATETIME,
                        severity TEXT DEFAULT 'Info',
                        FOREIGN KEY (target_id) REFERENCES targets(id)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        type TEXT,
                        value TEXT UNIQUE,
                        metadata TEXT,
                        first_seen DATETIME
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS relations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_id INTEGER,
                        target_id INTEGER,
                        type TEXT,
                        strength FLOAT DEFAULT 1.0,
                        timestamp DATETIME,
                        FOREIGN KEY (source_id) REFERENCES entities(id),
                        FOREIGN KEY (target_id) REFERENCES entities(id),
                        UNIQUE(source_id, target_id, type)
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS global_state (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at DATETIME
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS gui_sessions (
                        session_id TEXT PRIMARY KEY,
                        name TEXT,
                        created_at TEXT,
                        updated_at TEXT,
                        targets TEXT,
                        settings TEXT,
                        agent_state TEXT,
                        status TEXT DEFAULT 'active'
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS gui_jobs (
                        job_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        target_id TEXT,
                        type TEXT,
                        status TEXT DEFAULT 'queued',
                        agent_state TEXT,
                        current_node TEXT,
                        progress_pct INTEGER DEFAULT 0,
                        started_at TEXT,
                        completed_at TEXT,
                        error TEXT
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scan_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target TEXT,
                        scan_mode TEXT,
                        started_at TEXT,
                        completed_at TEXT,
                        findings_count INTEGER DEFAULT 0,
                        risk_score INTEGER DEFAULT 0,
                        report_path TEXT
                    )
                """)
                current = self._get_schema_version()
                if current < 2:
                    findings_cols = {row[1] for row in conn.execute("PRAGMA table_info(findings)").fetchall()}
                    if "severity" not in findings_cols:
                        conn.execute("ALTER TABLE findings ADD COLUMN severity TEXT DEFAULT 'Info'")
                if current < _SCHEMA_VERSION:
                    self._set_schema_version(_SCHEMA_VERSION)
                    logger.info("Schema upgraded to v%d", _SCHEMA_VERSION)
        except Exception as e:
            logger.error("Database init failed: %s", e)
            raise

    # ------------------------------------------------------------------
    # CRUD: Entities (Knowledge Graph nodes)
    # ------------------------------------------------------------------
    def upsert_entity(self, entity_type: str, value: str, metadata: Optional[dict] = None) -> int:
        """Upsert entity."""
        try:
            with self._get_conn() as conn:
                meta_json = json.dumps(metadata) if metadata else None
                now = datetime.now().isoformat()
                conn.execute(
                    """INSERT INTO entities (type, value, metadata, first_seen)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(value) DO UPDATE SET
                           metadata = COALESCE(excluded.metadata, entities.metadata)""",
                    (entity_type, value, meta_json, now),
                )
                row = conn.execute("SELECT id FROM entities WHERE value = ?", (value,)).fetchone()
                return row["id"] if row else -1
        except Exception as e:
            logger.error("upsert_entity(%s, %s) failed: %s", entity_type, value, e)
            return -1

    # ------------------------------------------------------------------
    # CRUD: Relations (Knowledge Graph edges)
    # ------------------------------------------------------------------
    def add_relation(self, source_val: str, target_val: str, rel_type: str, strength: float = 1.0) -> None:
        """Add relation."""
        try:
            with self._get_conn() as conn:
                s_row = conn.execute("SELECT id FROM entities WHERE value = ?", (source_val,)).fetchone()
                t_row = conn.execute("SELECT id FROM entities WHERE value = ?", (target_val,)).fetchone()
                if s_row and t_row:
                    now = datetime.now().isoformat()
                    conn.execute(
                        """INSERT INTO relations (source_id, target_id, type, strength, timestamp)
                           VALUES (?, ?, ?, ?, ?)
                           ON CONFLICT(source_id, target_id, type) DO UPDATE SET
                               strength = MAX(relations.strength, excluded.strength),
                               timestamp = excluded.timestamp""",
                        (s_row["id"], t_row["id"], rel_type, strength, now),
                    )
        except Exception as e:
            logger.error("add_relation(%s, %s, %s) failed: %s", source_val, target_val, rel_type, e)

    # ------------------------------------------------------------------
    # CRUD: Graph insights
    # ------------------------------------------------------------------
    def get_graph_insights(self) -> str:
        """Get graph insights."""
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """SELECT e1.value, r.type, e2.value
                       FROM relations r
                       JOIN entities e1 ON r.source_id = e1.id
                       JOIN entities e2 ON r.target_id = e2.id
                       ORDER BY r.timestamp DESC
                       LIMIT 100"""
                ).fetchall()
                return "\n".join(f"({s}) --[{t}]--> ({o})" for s, t, o in rows)
        except Exception as e:
            logger.error("get_graph_insights failed: %s", e)
            return ""

    # ------------------------------------------------------------------
    # CRUD: Targets
    # ------------------------------------------------------------------
    def upsert_target(self, domain: str, parent_domain: Optional[str] = None, priority: int = 0) -> None:
        """Upsert target."""
        try:
            with self._get_conn() as conn:
                now = datetime.now().isoformat()
                conn.execute(
                    """INSERT INTO targets (domain, parent_domain, priority, last_seen)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(domain) DO UPDATE SET
                           last_seen = excluded.last_seen,
                           priority = MAX(targets.priority, excluded.priority)""",
                    (domain, parent_domain, priority, now),
                )
        except Exception as e:
            logger.error("upsert_target(%s) failed: %s", domain, e)

    # ------------------------------------------------------------------
    # CRUD: Findings
    # ------------------------------------------------------------------
    def add_finding(
        self, domain: str, tool_name: str, data_type: str, raw_data: str, summary: str,
        severity: str = "Info",
    ) -> None:
        """Add finding."""
        try:
            with self._get_conn() as conn:
                row = conn.execute("SELECT id FROM targets WHERE domain = ?", (domain,)).fetchone()
                if row:
                    target_id = row["id"]
                else:
                    now = datetime.now().isoformat()
                    conn.execute(
                        "INSERT INTO targets (domain, last_seen) VALUES (?, ?)",
                        (domain, now),
                    )
                    row = conn.execute("SELECT id FROM targets WHERE domain = ?", (domain,)).fetchone()
                    target_id = row["id"] if row else -1
                if target_id < 0:
                    logger.warning("add_finding: could not resolve target for %s", domain)
                    return
                now = datetime.now().isoformat()
                conn.execute(
                    """INSERT INTO findings (target_id, tool_name, data_type, raw_data, summary, timestamp, severity)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (target_id, tool_name, data_type, raw_data, summary, now, severity),
                )
        except Exception as e:
            logger.error("add_finding(%s, %s) failed: %s", domain, tool_name, e)

    def get_detailed_findings(self, domain: str, since: Optional[str] = None) -> list[dict]:
        """
        Per-domain findings as plain dicts, optionally filtered to those
        recorded at or after `since` (an ISO timestamp string).

        Added 2026-07-18 for the opt-in experimental_agent module
        (app/modules/experimental_agent/), ported from the momen branch,
        which calls this for session-scoped result filtering.
        """
        try:
            with self._get_conn() as conn:
                query = (
                    "SELECT f.tool_name, f.data_type, f.raw_data, f.summary, f.timestamp, f.severity "
                    "FROM findings f JOIN targets t ON f.target_id = t.id "
                    "WHERE t.domain = ?"
                )
                params: list[Any] = [domain]
                if since:
                    query += " AND f.timestamp >= ?"
                    params.append(since)
                query += " ORDER BY f.timestamp ASC"
                rows = conn.execute(query, params).fetchall()
        except Exception as e:
            logger.error("get_detailed_findings(%s) failed: %s", domain, e)
            return []

        return [
            {
                "tool_name": row["tool_name"],
                "data_type": row["data_type"],
                "raw_data": row["raw_data"],
                "summary": row["summary"],
                "timestamp": row["timestamp"],
                "severity": row["severity"] or "Info",
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # CRUD: Blackboard summary
    # ------------------------------------------------------------------
    def get_blackboard_summary(self, max_chars: int = 3000) -> str:
        """Build a JSON summary of Blackboard findings, bounded to `max_chars`.

        Feeds directly into LLM prompts in several places (ArgusBrain's
        context fusion, the `Query_Memory` tool's own return value,
        `reflective_verification.py`'s TDA scoring) - all of them share
        this one query instead of each re-deriving their own bound
        (Constitution IX). Unbounded, this grows with every finding ever
        recorded across every target, not just the one being analyzed -
        live testing (specs/018) hit Ollama's context-size limit and, at
        an incautious `num_ctx` increase, crashed the GPU process outright
        (VRAM-constrained hardware). Per RAG token-budget best practice,
        rows are added in existing priority/recency order until the next
        one would exceed `max_chars`, then stopped - never truncated
        mid-entry, which would both break the JSON and cut a finding's
        text off mid-sentence.

        Args:
            max_chars (int): Maximum length of the returned JSON string.
                Default 3000 is a conservative budget that comfortably
                fits even a cautious `num_ctx` alongside the rest of the
                system prompt, tool descriptions, and conversation history.

        Returns:
            str: A JSON object (`{domain: {data_type: summary}}`), never
            longer than `max_chars`. `"{}"` on any error or if there are
            no findings yet.
        """
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """SELECT t.domain, f.data_type, f.summary
                       FROM targets t
                       JOIN findings f ON t.id = f.target_id
                       ORDER BY t.priority DESC, f.timestamp DESC"""
                ).fetchall()
                summary: dict[str, dict[str, str]] = {}
                for domain, dtype, smry in rows:
                    candidate = dict(summary)
                    candidate.setdefault(domain, dict(summary.get(domain, {})))
                    if dtype in candidate[domain]:
                        continue
                    candidate[domain][dtype] = smry
                    if len(json.dumps(candidate, indent=2)) > max_chars and summary:
                        break
                    summary = candidate
                return json.dumps(summary, indent=2)
        except Exception as e:
            logger.error("get_blackboard_summary failed: %s", e)
            return "{}"

    def summarize_for_planning(self, k: int = 3, max_chars: int = 3000) -> str:
        """Per-source (tool_name), bounded-k aggregation across all targets (specs/019).

        Additive to, and does not replace, `get_blackboard_summary()` above -
        that method's `{domain: {data_type: summary}}` shape (one survivor
        per domain+data_type pair) is relied on verbatim by existing callers/
        tests (`tests/test_memory.py::test_add_finding_multiple_types` et
        al.), so it is left untouched. This method instead adapts the
        Red-MIRROR paper's SRMM `GetAggregatedContext(k)` (Algorithm 2) to
        Argus's actual schema: the paper partitions by execution agent;
        Argus's closest existing analog to "which agent produced this" is
        `findings.tool_name`, not `data_type` - so this groups by
        `(domain, tool_name)` and keeps the `k` most recent findings per
        group, each formatted with an explicit `[tool_name]` prefix so
        provenance is visible to the LLM (the paper's `Format` step), unlike
        `get_blackboard_summary()`'s existing shape, which drops `tool_name`
        from its output entirely.

        Args:
            k (int): Max findings kept per `(domain, tool_name)` group.
                Default 3, matching the paper's own default.
            max_chars (int): Safety-net truncation, matching
                `get_blackboard_summary()`'s convention - `k` bounding
                should make this rare in practice, not the primary bound.

        Returns:
            str: Newline-joined `"[tool_name] domain data_type: summary"`
            lines, most-recent-first per group, or the paper's own
            `"No shared memory available."` string if there are no
            findings yet (matching SRMM's Algorithm 2 fallback verbatim).
        """
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """SELECT t.domain, f.tool_name, f.data_type, f.summary
                       FROM targets t
                       JOIN findings f ON t.id = f.target_id
                       ORDER BY t.priority DESC, f.tool_name ASC, f.timestamp DESC, f.id DESC"""
                ).fetchall()
                seen_per_group: dict[tuple[str, str], int] = {}
                lines: list[str] = []
                total_len = 0
                for domain, tool_name, dtype, smry in rows:
                    group_key = (domain, tool_name)
                    count = seen_per_group.get(group_key, 0)
                    if count >= k:
                        continue
                    seen_per_group[group_key] = count + 1
                    line = f"[{tool_name}] {domain} {dtype}: {smry}"
                    if lines and total_len + len(line) + 1 > max_chars:
                        break
                    lines.append(line)
                    total_len += len(line) + 1
                return "\n".join(lines) if lines else "No shared memory available."
        except Exception as e:
            logger.error("summarize_for_planning failed: %s", e)
            return "No shared memory available."

    def get_blackboard_counts(self) -> dict:
        """Dict-shaped summary (target_count/findings_count) for the GUI status
        bar. get_blackboard_summary() above returns a JSON *string* of nested
        per-domain detail - callers that need simple counts should use this
        instead of misusing that string as a dict.
        """
        try:
            with self._get_conn() as conn:
                target_count = conn.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
                findings_count = conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
                return {"target_count": target_count, "findings_count": findings_count}
        except Exception as e:
            logger.error("get_blackboard_counts failed: %s", e)
            return {"target_count": 0, "findings_count": 0}

    def get_findings_graph_rows(self) -> list[tuple[str, str, str, str]]:
        """(domain, tool_name, data_type, summary) rows for the Knowledge Graph
        tab - built from the same targets/findings tables the tactical agent's
        recon/scanner nodes actually write to via upsert_target()/add_finding().
        """
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """SELECT t.domain, f.tool_name, f.data_type, f.summary
                       FROM targets t
                       JOIN findings f ON t.id = f.target_id
                       ORDER BY f.timestamp DESC"""
                ).fetchall()
                return [tuple(row) for row in rows]
        except Exception as e:
            logger.error("get_findings_graph_rows failed: %s", e)
            return []

    # ------------------------------------------------------------------
    # Purge polluted entries (surgical - not a full wipe)
    # ------------------------------------------------------------------
    @staticmethod
    def _looks_like_garbage_domain(domain: Optional[str]) -> bool:
        """
        Real domains never contain whitespace or quotes, and are never
        anywhere close to 100+ characters long. Entries this shape are
        leftover pollution from a fixed bug where a full GUI instruction
        paragraph ("CONSULT MEMORY FIRST using 'Query_Memory'. Then
        perform a comprehensive security analysis for...") got passed
        through and stored as if it were the target/domain itself.
        """
        if not domain:
            return True
        if " " in domain or "'" in domain or '"' in domain:
            return True
        if len(domain) > 100:
            return True
        return False

    def purge_invalid_targets(self) -> int:
        """
        Removes only targets (and their findings) whose domain matches
        _looks_like_garbage_domain() - unlike clear_memory(), this leaves
        every legitimately-scanned target's data untouched. Returns the
        number of garbage targets removed.
        """
        removed = 0
        try:
            with self._get_conn() as conn:
                rows = conn.execute("SELECT id, domain FROM targets").fetchall()
                bad_ids = [
                    row["id"] for row in rows
                    if self._looks_like_garbage_domain(row["domain"])
                ]
                for target_id in bad_ids:
                    conn.execute("DELETE FROM findings WHERE target_id = ?", (target_id,))
                    conn.execute("DELETE FROM targets WHERE id = ?", (target_id,))
                    removed += 1
            logger.info("Purged %d polluted target(s) from memory", removed)
        except Exception as e:
            logger.error("purge_invalid_targets failed: %s", e)
        return removed

    # ------------------------------------------------------------------
    # Scan sessions (logging dashboard / history)
    # ------------------------------------------------------------------
    def log_scan_session(
        self, target: str, mode: str, started_at: str, completed_at: Optional[str] = None,
        findings_count: int = 0, risk_score: int = 0, report_path: Optional[str] = None,
    ) -> None:
        """Log scan session."""
        try:
            with self._get_conn() as conn:
                conn.execute(
                    """INSERT INTO scan_sessions
                       (target, scan_mode, started_at, completed_at, findings_count, risk_score, report_path)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (target, mode, started_at, completed_at, findings_count, risk_score, report_path),
                )
        except Exception as e:
            logger.error("log_scan_session(%s) failed: %s", target, e)

    def get_scan_history(self, limit: int = 50) -> list[dict]:
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """SELECT target, scan_mode, started_at, completed_at,
                              findings_count, risk_score, report_path
                       FROM scan_sessions ORDER BY started_at DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
        except Exception as e:
            logger.error("get_scan_history failed: %s", e)
            return []
        return [
            {
                "target": row["target"], "mode": row["scan_mode"],
                "started": row["started_at"], "completed": row["completed_at"],
                "findings": row["findings_count"], "risk_score": row["risk_score"],
                "report": row["report_path"],
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Target prioritization
    # ------------------------------------------------------------------
    def get_priority_targets(self, limit: int = 10) -> str:
        """
        Formatted list of the highest-priority already-recorded targets, for
        direct inclusion in an agent's context - filters out garbage/error
        strings the same way _looks_like_garbage_domain() does elsewhere.
        """
        try:
            with self._get_conn() as conn:
                rows = conn.execute(
                    """SELECT domain FROM targets
                       ORDER BY priority DESC, last_seen DESC LIMIT ?""",
                    (limit * 3,),
                ).fetchall()
        except Exception as e:
            logger.error("get_priority_targets failed: %s", e)
            return "No prioritized targets in memory yet."
        if not rows:
            return "No prioritized targets in memory yet."
        targets = [
            row["domain"] for row in rows
            if row["domain"] and "." in row["domain"]
            and not any(b in row["domain"].lower() for b in _PRIORITY_TARGET_BAD_SUBSTRINGS)
        ][:limit]
        if not targets:
            return "No valid targets in memory yet."
        return "TOP PRIORITY TARGETS:\n" + "\n".join(
            f"{i + 1}. {t}" for i, t in enumerate(targets)
        )

    # ------------------------------------------------------------------
    # Clear memory
    # ------------------------------------------------------------------
    def clear_memory(self) -> None:
        backup = self.db_path + ".bak"
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, backup)
                os.remove(self.db_path)
            self._init_db()
            logger.info("Memory cleared (backup at %s)", backup)
        except Exception as e:
            logger.error("clear_memory failed: %s", e)
            if os.path.exists(backup):
                shutil.copy2(backup, self.db_path)
                logger.info("Restored from backup after failed clear")