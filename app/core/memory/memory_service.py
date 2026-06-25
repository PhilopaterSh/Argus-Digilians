import sqlite3
import json
import os
from datetime import datetime

class ArgusMemory:
    def __init__(self, db_path="data/argus_intelligence.db"):
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for targets and their discovery status
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

        # Table for technical findings (Blackboard)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                tool_name TEXT,
                data_type TEXT, -- 'waf', 'tech', 'ports', 'headers'
                raw_data TEXT,
                summary TEXT,
                timestamp DATETIME,
                FOREIGN KEY (target_id) REFERENCES targets(id)
            )
        ''')

        # [NEW] Knowledge Graph Nodes (Entities)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, -- 'domain', 'ip', 'email', 'key', 'tech', 'software', 'vulnerability'
                value TEXT UNIQUE,
                metadata TEXT, -- JSON storage for extra details
                first_seen DATETIME
            )
        ''')

        # [NEW] Knowledge Graph Edges (Relationships)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                target_id INTEGER,
                type TEXT, -- 'HOSTS', 'USES_TECH', 'HAS_FILE', 'SHARED_CREDENTIAL', 'LINKED_TO'
                strength FLOAT DEFAULT 1.0,
                timestamp DATETIME,
                FOREIGN KEY (source_id) REFERENCES entities(id),
                FOREIGN KEY (target_id) REFERENCES entities(id),
                UNIQUE(source_id, target_id, type)
            )
        ''')

        # Table for global AI-ready summaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS global_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    def upsert_entity(self, entity_type, value, metadata=None):
        """Adds or updates a node in the Knowledge Graph."""
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
        """Creates a link (Edge) between two entities in the Graph."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        try:
            # Ensure entities exist
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
        """Returns a high-level overview of entity relationships for AI reasoning."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query for cross-target commonalities
        cursor.execute('''
            SELECT e1.value, r.type, e2.value
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            ORDER BY r.timestamp DESC
            LIMIT 100
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        insights = []
        for s, t, o in rows:
            insights.append(f"({s}) --[{t}]--> ({o})")
            
        return "\n".join(insights)


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

    def add_finding(self, domain, tool_name, data_type, raw_data, summary):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get target_id
        cursor.execute('SELECT id FROM targets WHERE domain = ?', (domain,))
        row = cursor.fetchone()
        if not row:
            self.upsert_target(domain)
            cursor.execute('SELECT id FROM targets WHERE domain = ?', (domain,))
            row = cursor.fetchone()
        
        target_id = row[0]
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO findings (target_id, tool_name, data_type, raw_data, summary, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (target_id, tool_name, data_type, raw_data, summary, now))
        
        conn.commit()
        conn.close()

    def get_blackboard_summary(self):
        """Returns a condensed view of all intelligence for the AI Agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.domain, f.data_type, f.summary 
            FROM targets t
            JOIN findings f ON t.id = f.target_id
            ORDER BY t.priority DESC, f.timestamp DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        summary = {}
        for domain, dtype, smry in rows:
            if domain not in summary:
                summary[domain] = {}
            if dtype not in summary[domain]:
                summary[domain][dtype] = smry
                
        return json.dumps(summary, indent=2)

    def clear_memory(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self._init_db()
