import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime


def get_db_path():
    """Returns a writable database path, falling back to user home if needed."""
    # Try project root first
    project_root = Path(__file__).parent.parent
    db_candidate = project_root / "argus_intelligence.db"
    try:
        # Test write access
        test_file = project_root / ".write_test"
        test_file.touch()
        test_file.unlink()
        return str(db_candidate)
    except (PermissionError, OSError):
        # Fallback to user home directory
        fallback = Path.home() / ".argus" / "argus_intelligence.db"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        print(f"[!] Project root not writable. Using fallback DB: {fallback}")
        return str(fallback)


class ArgusMemory:
    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        # Validate the DB with a connection that is ALWAYS closed, so that if the
        # file is malformed we can remove it (an open handle would lock the file
        # on Windows and block the rebuild).
        if not self._db_ok():
            self._reset_corrupt_db()
        self._init_db()

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

    def _reset_corrupt_db(self):
        """Handle a malformed SQLite file: keep the bad file as *.corrupt
        (for inspection) and clear any side files so a clean DB can be built."""
        for suffix in ("", "-journal", "-wal", "-shm"):
            p = self.db_path + suffix
            try:
                if not os.path.exists(p):
                    continue
                if suffix == "":
                    try:
                        os.replace(p, p + ".corrupt")   # back up the bad DB
                        continue
                    except OSError:
                        pass
                os.remove(p)
            except OSError:
                pass
        print("[!] Corrupt database detected -> rebuilt a fresh argus_intelligence.db "
              "(old file saved as argus_intelligence.db.corrupt).")

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                parent_domain TEXT,
                status TEXT DEFAULT 'discovered',
                priority INTEGER DEFAULT 0,
                last_seen DATETIME
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                tool_name TEXT,
                data_type TEXT,
                raw_data TEXT,
                summary TEXT,
                severity TEXT DEFAULT 'Info',
                timestamp DATETIME,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                value TEXT UNIQUE,
                metadata TEXT,
                first_seen DATETIME
            )
        ''')

        cursor.execute('''
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
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                scan_mode TEXT,
                started_at DATETIME,
                completed_at DATETIME,
                findings_count INTEGER DEFAULT 0,
                risk_score INTEGER DEFAULT 0,
                report_path TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def upsert_entity(self, entity_type, value, metadata=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        meta_json = json.dumps(metadata) if metadata else None
        cursor.execute('''
            INSERT INTO entities (type, value, metadata, first_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(value) DO UPDATE SET
                metadata = COALESCE(excluded.metadata, entities.metadata)
        ''', (entity_type, value, meta_json, now))
        cursor.execute('SELECT id FROM entities WHERE value = ?', (value,))
        entity_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return entity_id

    def add_relation(self, source_val, target_val, rel_type, strength=1.0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        try:
            cursor.execute('SELECT id FROM entities WHERE value = ?', (source_val,))
            s_row = cursor.fetchone()
            cursor.execute('SELECT id FROM entities WHERE value = ?', (target_val,))
            t_row = cursor.fetchone()
            if s_row and t_row:
                cursor.execute('''
                    INSERT INTO relations (source_id, target_id, type, strength, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(source_id, target_id, type) DO UPDATE SET
                        strength = MAX(relations.strength, excluded.strength),
                        timestamp = excluded.timestamp
                ''', (s_row[0], t_row[0], rel_type, strength, now))
        except Exception as e:
            print(f"[!] Graph Error: {e}")
        finally:
            conn.commit()
            conn.close()

    def get_graph_insights(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e1.value, r.type, e2.value
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            ORDER BY r.timestamp DESC LIMIT 100
        ''')
        rows = cursor.fetchall()
        conn.close()
        insights = [f"({s}) --[{t}]--> ({o})" for s, t, o in rows]
        return "\n".join(insights) if insights else "No knowledge graph data yet."

    def upsert_target(self, domain, parent_domain=None, priority=0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO targets (domain, parent_domain, priority, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                last_seen = excluded.last_seen,
                priority = MAX(targets.priority, excluded.priority)
        ''', (domain, parent_domain, priority, now))
        conn.commit()
        conn.close()

    def add_finding(self, domain, tool_name, data_type, raw_data, summary, severity="Info"):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM targets WHERE domain = ?', (domain,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            self.upsert_target(domain)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM targets WHERE domain = ?', (domain,))
            row = cursor.fetchone()
        target_id = row[0]
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO findings (target_id, tool_name, data_type, raw_data, summary, severity, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (target_id, tool_name, data_type, raw_data, summary, severity, now))
        conn.commit()
        conn.close()

    def get_blackboard_summary(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.domain, f.data_type, f.summary, f.severity, f.raw_data
            FROM targets t
            JOIN findings f ON t.id = f.target_id
            ORDER BY t.priority DESC, f.timestamp DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        summary = {}
        for domain, dtype, smry, sev, raw in rows:
            if domain not in summary:
                summary[domain] = {}
            if dtype not in summary[domain]:
                # raw_data is additive (PoC/evidence detail for vulnerability
                # findings) — existing consumers that only read
                # "summary"/"severity" are unaffected.
                entry = {"summary": smry, "severity": sev}
                if raw and raw != smry:
                    entry["raw_data"] = raw[:2000]
                summary[domain][dtype] = entry
        return json.dumps(summary, indent=2)

    def get_scan_history(self, limit=50):
        """Returns recent scan sessions for the logging dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT target, scan_mode, started_at, completed_at,
                   findings_count, risk_score, report_path
            FROM scan_sessions
            ORDER BY started_at DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        sessions = []
        for row in rows:
            sessions.append({
                "target": row[0], "mode": row[1],
                "started": row[2], "completed": row[3],
                "findings": row[4], "risk_score": row[5],
                "report": row[6]
            })
        return sessions

    def log_scan_session(self, target, mode, started_at, completed_at=None,
                         findings_count=0, risk_score=0, report_path=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scan_sessions
            (target, scan_mode, started_at, completed_at, findings_count, risk_score, report_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (target, mode, started_at, completed_at, findings_count, risk_score, report_path))
        conn.commit()
        conn.close()

    def clear_memory(self):
        """Wipe all data without deleting the file.

        On Windows, SQLite holds a shared lock on the .db file while the process
        is running, so os.remove() raises PermissionError. Truncating via SQL
        DELETE avoids the lock entirely and is safe with concurrent connections.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Get all user-created tables and wipe them
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        for tbl in tables:
            cursor.execute(f"DELETE FROM {tbl}")
        conn.commit()
        conn.close()
        # Re-init ensures the schema is still valid after the wipe
        self._init_db()

    def purge_bad_entities(self):
        """Remove stale WSL error strings stored as entities/targets."""
        BAD = ("Error", "---", "Code 127", "Code 2", "Suggestion:", "not found",
               "command not", "permission denied")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for pat in BAD:
            cursor.execute("DELETE FROM targets WHERE domain LIKE ?", (f"%{pat}%",))
            cursor.execute("DELETE FROM entities WHERE value LIKE ?", (f"%{pat}%",))
            cursor.execute("""DELETE FROM relations WHERE source_id IN
                (SELECT id FROM entities WHERE value LIKE ?)
                OR target_id IN (SELECT id FROM entities WHERE value LIKE ?)""",
                (f"%{pat}%", f"%{pat}%"))
        conn.commit()
        conn.close()

    def get_priority_targets(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        BAD = ("error", "---", "code ", "suggestion:", "not found", "command")

        cursor.execute('''
            SELECT domain FROM targets
            ORDER BY priority DESC, last_seen DESC
            LIMIT ?
        ''', (limit * 3,))  # fetch extra to filter
        rows = cursor.fetchall()
        conn.close()
        if not rows:
            return "No prioritized targets in memory yet."
        targets = [
            row[0] for row in rows
            if row[0] and '.' in row[0]
            and not any(b in row[0].lower() for b in BAD)
        ][:limit]
        if not targets:
            return "No valid targets in memory yet."
        return "TOP PRIORITY TARGETS:\n" + "\n".join(
            f"{i+1}. {t}" for i, t in enumerate(targets)
        )
