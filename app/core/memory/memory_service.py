from core.memory.database import SQLiteDatabase
from core.memory.finding_store import FindingStore
from core.memory.graph_store import GraphStore
from core.memory.summary_service import SummaryService
from core.memory.target_store import TargetStore


class ArgusMemory:
    """
    Main memory facade for Argus intelligence storage.

    This class provides a clean public API for the rest of the application while
    delegating the actual database operations to focused store/service classes.

    It preserves compatibility with the original ArgusMemory interface, but the
    internal implementation now follows Separation of Concerns.

    Responsibilities:
        - Initialize the database layer.
        - Initialize memory-related stores and services.
        - Expose a simple public API for targets, findings, graph data, summaries,
          and memory reset operations.

    This class should not contain:
        - SQL schema creation logic.
        - Direct SQL queries.
        - Knowledge graph query logic.
        - Finding insertion logic.
        - Summary-building logic.

    Those responsibilities are delegated to:
        - SQLiteDatabase
        - TargetStore
        - FindingStore
        - GraphStore
        - SummaryService
    """

    def __init__(self, db_path: str = "argus_intelligence.db"):
        """
        Initialize the Argus memory facade.

        Args:
            db_path:
                Path to the SQLite database file used to store Argus intelligence.
        """

        # Initialize the database manager.
        # This handles connection creation and schema initialization.
        self.database = SQLiteDatabase(db_path)

        # Initialize the target store.
        # Responsible for target/domain-related database operations.
        self.targets = TargetStore(self.database)

        # Initialize the findings store.
        # It depends on TargetStore because each finding must be linked to a target.
        self.findings = FindingStore(
            database=self.database,
            target_store=self.targets,
        )

        # Initialize the knowledge graph store.
        # Responsible for entities and relations.
        self.graph = GraphStore(self.database)

        # Initialize the summary service.
        # Responsible for blackboard summaries and graph insights.
        self.summary = SummaryService(self.database)

    def upsert_target(
        self,
        domain: str,
        parent_domain: str | None = None,
        priority: int = 0,
    ) -> None:
        """
        Insert or update a target record.

        Args:
            domain:
                Domain, subdomain, IP address, or asset identifier.

            parent_domain:
                Optional parent domain for subdomains.

            priority:
                Target priority score used for sorting and analysis focus.

        Returns:
            None
        """

        return self.targets.upsert_target(
            domain=domain,
            parent_domain=parent_domain,
            priority=priority,
        )

    def add_finding(
        self,
        domain: str,
        tool_name: str,
        data_type: str,
        raw_data: str,
        summary: str,
    ) -> None:
        """
        Add a technical finding for a target.

        Args:
            domain:
                Domain, subdomain, IP address, or asset related to the finding.

            tool_name:
                Name of the tool that generated the finding.
                Example: "nmap", "nikto", "ffuf", "whatweb".

            data_type:
                Type/category of the collected data.
                Example: "ports", "headers", "tech", "vulnerability", "secrets".

            raw_data:
                Full raw output from the tool.

            summary:
                Short summary of the finding for quick AI/human review.

        Returns:
            None
        """

        return self.findings.add_finding(
            domain=domain,
            tool_name=tool_name,
            data_type=data_type,
            raw_data=raw_data,
            summary=summary,
        )

    def upsert_entity(
        self,
        entity_type: str,
        value: str,
        metadata: dict | None = None,
    ) -> int:
        """
        Insert or update a knowledge graph entity.

        Args:
            entity_type:
                Type of entity.
                Example: "domain", "ip", "tech", "secret", "file", "vulnerability".

            value:
                Unique entity value.

            metadata:
                Optional extra metadata stored as JSON.

        Returns:
            int:
                Database ID of the inserted or existing entity.
        """

        return self.graph.upsert_entity(
            entity_type=entity_type,
            value=value,
            metadata=metadata,
        )

    def add_relation(
        self,
        source_val: str,
        target_val: str,
        rel_type: str,
        strength: float = 1.0,
    ) -> None:
        """
        Create or update a relationship between two knowledge graph entities.

        Args:
            source_val:
                Source entity value.

            target_val:
                Target entity value.

            rel_type:
                Relationship type.
                Example: "HOSTS", "USES_TECH", "EXPOSES", "HAS_FILE".

            strength:
                Confidence or importance score for the relationship.

        Returns:
            None
        """

        return self.graph.add_relation(
            source_val=source_val,
            target_val=target_val,
            rel_type=rel_type,
            strength=strength,
        )

    def get_blackboard_summary(self) -> str:
        """
        Return a condensed summary of all stored findings.

        This is usually consumed by the AI agent to understand the current
        intelligence state before generating a report.

        Returns:
            str:
                JSON-formatted summary of targets and findings.
        """

        return self.summary.get_blackboard_summary()

    def get_graph_insights(self) -> str:
        """
        Return knowledge graph relationship insights.

        This provides the AI agent with cross-target relationships such as shared
        infrastructure, common technologies, exposed files, or linked secrets.

        Returns:
            str:
                Human-readable graph relationship summary.
        """

        return self.summary.get_graph_insights()

    def clear_memory(self) -> None:
        """
        Clear the memory database and recreate the schema.

        Useful for development, testing, or starting a fresh intelligence
        collection session.

        Returns:
            None
        """

        return self.database.clear()