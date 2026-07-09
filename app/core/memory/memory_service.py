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
_SCHEMA_VERSION = 1


class ArgusMemory:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        if self.db_path != ":memory:":
            self._migrate_from_root()
        self._init_db()
        if self.db_path != ":memory:":
            self._verify_integrity()

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
        try:
            with self._get_conn() as conn:
                row = conn.execute("PRAGMA user_version").fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def _set_schema_version(self, version: int) -> None:
        try:
            with self._get_conn() as conn:
                conn.execute(f"PRAGMA user_version = {version}")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Database initialization
    # ------------------------------------------------------------------
    def _init_db(self) -> None:
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
                current = self._get_schema_version()
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
    def add_finding(self, domain: str, tool_name: str, data_type: str, raw_data: str, summary: str) -> None:
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
                    """INSERT INTO findings (target_id, tool_name, data_type, raw_data, summary, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (target_id, tool_name, data_type, raw_data, summary, now),
                )
        except Exception as e:
            logger.error("add_finding(%s, %s) failed: %s", domain, tool_name, e)

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
