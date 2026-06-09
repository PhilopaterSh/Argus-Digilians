import json
from datetime import datetime
from typing import Any


class GraphStore:
    """
    Data-access layer for knowledge graph entities and relations.

    This class is responsible only for operations related to the knowledge graph
    tables:

        - entities
        - relations

    The knowledge graph allows Argus to store relationships between discovered
    assets, technologies, IP addresses, files, secrets, vulnerabilities, and
    other security-relevant entities.

    Example relationships:
        - domain.com --[HOSTS]--> 192.168.1.10
        - app.domain.com --[USES_TECH]--> Apache
        - api.domain.com --[EXPOSES]--> API Key
        - domain.com --[PROTECTED_BY]--> Cloudflare

    This class should not contain:
        - Reconnaissance logic.
        - Vulnerability scanning logic.
        - Report generation logic.
        - Agent or LLM logic.
    """

    def __init__(self, database):
        """
        Initialize the graph store.

        Args:
            database:
                Database manager that provides managed SQLite sessions.
        """

        # Database dependency used for opening managed SQLite sessions.
        self.database = database

    def upsert_entity(
        self,
        entity_type: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Insert or update a knowledge graph entity.

        If the entity already exists, its metadata is updated only when new
        metadata is provided. If no new metadata is provided, the existing
        metadata remains unchanged.

        Args:
            entity_type:
                Type/category of the entity.
                Example: "domain", "ip", "tech", "secret", "file", "vulnerability".

            value:
                Unique value of the entity.
                Example: "example.com", "192.168.1.10", "Apache", "CVE-2024-xxxx".

            metadata:
                Optional dictionary containing extra entity details. It is stored
                as a JSON string in the database.

        Returns:
            int:
                Database ID of the inserted or existing entity.
        """

        # Generate a timestamp for newly discovered entities.
        now = datetime.now().isoformat()

        # Convert metadata dictionary to JSON for SQLite text storage.
        metadata_json = json.dumps(metadata) if metadata else None

        with self.database.session() as conn:
            cursor = conn.cursor()

            # Insert the entity if it does not exist.
            # If it already exists, update metadata only when new metadata is provided.
            cursor.execute(
                """
                INSERT INTO entities (type, value, metadata, first_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(value) DO UPDATE SET
                    metadata = COALESCE(excluded.metadata, entities.metadata)
                """,
                (
                    entity_type,
                    value,
                    metadata_json,
                    now,
                ),
            )

            # Retrieve and return the entity ID after insert/update.
            cursor.execute(
                "SELECT id FROM entities WHERE value = ?",
                (value,),
            )

            row = cursor.fetchone()

            if row is None:
                raise RuntimeError(f"Failed to insert or retrieve entity: {value}")

            return row[0]

    def add_relation(
        self,
        source_val: str,
        target_val: str,
        rel_type: str,
        strength: float = 1.0,
    ) -> None:
        """
        Create or update a relationship between two existing entities.

        The source and target entities must already exist in the `entities`
        table. If either entity is missing, the relation is skipped.

        If the same relation already exists, the strongest value is preserved,
        and the timestamp is refreshed.

        Args:
            source_val:
                Value of the source entity.
                Example: "app.example.com".

            target_val:
                Value of the target entity.
                Example: "Apache".

            rel_type:
                Type of relationship between the two entities.
                Example: "HOSTS", "USES_TECH", "EXPOSES", "PROTECTED_BY", "HAS_FILE".

            strength:
                Confidence or importance score of the relationship.
                Default is 1.0.

        Returns:
            None
        """

        # Generate a timestamp for the relationship insert/update.
        now = datetime.now().isoformat()

        with self.database.session() as conn:
            cursor = conn.cursor()

            # Resolve source entity ID.
            cursor.execute(
                "SELECT id FROM entities WHERE value = ?",
                (source_val,),
            )
            source_row = cursor.fetchone()

            # Resolve target entity ID.
            cursor.execute(
                "SELECT id FROM entities WHERE value = ?",
                (target_val,),
            )
            target_row = cursor.fetchone()

            # Skip relation creation if either entity does not exist.
            # This avoids invalid foreign-key references.
            if not source_row or not target_row:
                return

            # Insert the relation if it does not exist.
            # If it already exists, keep the maximum strength and update timestamp.
            cursor.execute(
                """
                INSERT INTO relations (
                    source_id,
                    target_id,
                    type,
                    strength,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id, target_id, type) DO UPDATE SET
                    strength = MAX(relations.strength, excluded.strength),
                    timestamp = excluded.timestamp
                """,
                (
                    source_row[0],
                    target_row[0],
                    rel_type,
                    strength,
                    now,
                ),
            )