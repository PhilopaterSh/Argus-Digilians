from datetime import datetime


class TargetStore:
    """
    Data-access layer for target records.

    This class is responsible only for operations related to the `targets`
    table. A target can be a domain, subdomain, IP address, or any asset that
    Argus discovers during reconnaissance.

    Responsibilities:
        - Insert new targets.
        - Update existing targets.
        - Retrieve target IDs by domain.

    This class should not contain:
        - Database schema creation logic.
        - Finding storage logic.
        - Knowledge graph logic.
        - Reconnaissance or scanning logic.
        - Report generation logic.
    """

    def __init__(self, database):
        """
        Initialize the target store.

        Args:
            database:
                Database manager that provides managed SQLite sessions.
        """

        # Database dependency used for opening managed SQLite sessions.
        self.database = database

    def upsert_target(
        self,
        domain: str,
        parent_domain: str | None = None,
        priority: int = 0,
    ) -> None:
        """
        Insert or update a target record.

        If the target already exists, its `last_seen` timestamp is refreshed
        and the highest priority value is preserved.

        Args:
            domain:
                Domain, subdomain, IP address, or asset identifier.
                Example: "example.com", "api.example.com", "192.168.1.10".

            parent_domain:
                Optional parent/root domain for discovered subdomains.
                Example: "example.com" for "api.example.com".

            priority:
                Numeric priority score used to rank targets for analysis.

        Returns:
            None
        """

        # Generate an ISO timestamp for the target discovery/update time.
        now = datetime.now().isoformat()

        # Insert the target if it does not exist.
        # If it already exists, update last_seen and keep the highest priority.
        with self.database.session() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO targets (
                    domain,
                    parent_domain,
                    priority,
                    last_seen
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    priority = MAX(targets.priority, excluded.priority)
                """,
                (
                    domain,
                    parent_domain,
                    priority,
                    now,
                ),
            )

    def get_target_id(self, domain: str) -> int | None:
        """
        Retrieve the database ID of a target by domain.

        Args:
            domain:
                Domain, subdomain, IP address, or asset identifier.

        Returns:
            int | None:
                Target ID if the target exists, otherwise None.
        """

        # Query the targets table for the matching domain.
        with self.database.session() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM targets WHERE domain = ?",
                (domain,),
            )

            row = cursor.fetchone()

            # Return the target ID if found; otherwise return None.
            return row[0] if row else None