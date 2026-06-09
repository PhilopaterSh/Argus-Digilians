from datetime import datetime


class FindingStore:
    """
    Data-access layer for security findings.

    This class is responsible only for operations related to the `findings`
    table. It stores raw tool output, summarized findings, and metadata about
    which target the finding belongs to.

    Responsibilities:
        - Resolve the target ID for a given domain.
        - Create the target automatically if it does not already exist.
        - Insert new finding records into the database.

    This class should not contain:
        - Database schema creation logic.
        - Reconnaissance or scanning logic.
        - Knowledge graph logic.
        - Report generation logic.
    """

    def __init__(self, database, target_store):
        """
        Initialize the finding store.

        Args:
            database:
                Database manager that provides managed SQLite sessions.

            target_store:
                Target store used to resolve or create target records before
                attaching findings to them.
        """

        # Database dependency used for opening managed SQLite sessions.
        self.database = database

        # TargetStore dependency used to find or create target records.
        self.target_store = target_store

    def add_finding(
        self,
        domain: str,
        tool_name: str,
        data_type: str,
        raw_data: str,
        summary: str,
    ) -> None:
        """
        Add a new technical finding for a specific domain or target.

        If the domain does not already exist in the `targets` table, this method
        creates it first, then stores the finding using the generated target ID.

        Args:
            domain:
                Domain, subdomain, IP address, or asset related to the finding.

            tool_name:
                Name of the tool that produced the finding.
                Example: "nmap", "nikto", "ffuf", "whatweb", "curl".

            data_type:
                Category of the finding.
                Example: "ports", "headers", "tech", "vulnerability", "secrets".

            raw_data:
                Full raw output returned by the tool.

            summary:
                Short AI-readable or human-readable summary of the finding.

        Returns:
            None
        """

        # Try to resolve the target ID for the provided domain.
        target_id = self.target_store.get_target_id(domain)

        # If the target does not exist yet, create it first.
        if not target_id:
            self.target_store.upsert_target(domain)
            target_id = self.target_store.get_target_id(domain)

        # Generate an ISO-formatted timestamp for consistent database storage.
        now = datetime.now().isoformat()

        # Insert the finding using a managed database session.
        # The session context manager handles commit and connection cleanup.
        with self.database.session() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO findings (
                    target_id,
                    tool_name,
                    data_type,
                    raw_data,
                    summary,
                    timestamp
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    target_id,
                    tool_name,
                    data_type,
                    raw_data,
                    summary,
                    now,
                ),
            )