import json


class SummaryService:
    """
    Service responsible for building AI-ready memory summaries.

    This class reads stored intelligence from the database and converts it into
    compact formats that can be consumed by the AI agent.

    Responsibilities:
        - Build a blackboard-style summary of discovered findings.
        - Build a readable knowledge graph relationship summary.
        - Keep summary-generation logic separate from database storage logic.

    This class should not contain:
        - Database schema creation logic.
        - Insert/update operations for targets or findings.
        - Reconnaissance or scanning logic.
        - Agent or LLM logic.
    """

    def __init__(self, database):
        """
        Initialize the summary service.

        Args:
            database:
                Database manager that provides managed SQLite sessions.
        """

        # Database dependency used for reading stored intelligence.
        self.database = database

    def get_blackboard_summary(self) -> str:
        """
        Build a condensed JSON summary of target findings.

        The blackboard summary gives the AI agent a compact view of the current
        intelligence state. It groups findings by domain and data type.

        Example output:
            {
              "example.com": {
                "ports": "80/tcp open http, 443/tcp open https",
                "tech": "Apache, PHP, WordPress"
              }
            }

        Behavior:
            - Results are ordered by target priority and newest findings first.
            - For each domain and data type, only the first/latest summary is kept.
            - The final result is returned as formatted JSON text.

        Returns:
            str:
                JSON-formatted summary of stored target findings.
        """

        # Fetch all findings joined with their related targets.
        with self.database.session() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT t.domain, f.data_type, f.summary
                FROM targets t
                JOIN findings f ON t.id = f.target_id
                ORDER BY t.priority DESC, f.timestamp DESC
                """
            )

            rows = cursor.fetchall()

        # Group findings by domain and data type.
        summary = {}

        for domain, data_type, finding_summary in rows:
            # Create a domain entry if this is the first finding for the domain.
            if domain not in summary:
                summary[domain] = {}

            # Keep only the first summary for each data type.
            # Because the SQL query is ordered by newest timestamp first,
            # this usually preserves the most recent finding summary.
            if data_type not in summary[domain]:
                summary[domain][data_type] = finding_summary

        # Return the grouped summary as readable JSON for the AI agent.
        return json.dumps(summary, indent=2)

    def get_graph_insights(self) -> str:
        """
        Build a readable summary of knowledge graph relationships.

        This method converts stored graph relations into a simple text format
        that is easy for the AI agent to reason over.

        Example output:
            (example.com) --[HOSTS]--> (192.168.1.10)
            (app.example.com) --[USES_TECH]--> (Apache)
            (api.example.com) --[EXPOSES]--> (API Key)

        Returns:
            str:
                Human-readable knowledge graph relationship summary.
        """

        # Fetch the latest graph relationships with source and target values.
        with self.database.session() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT e1.value, r.type, e2.value
                FROM relations r
                JOIN entities e1 ON r.source_id = e1.id
                JOIN entities e2 ON r.target_id = e2.id
                ORDER BY r.timestamp DESC
                LIMIT 100
                """
            )

            rows = cursor.fetchall()

        # Convert each database relation into a readable graph expression.
        insights = []

        for source, relation_type, target in rows:
            insights.append(
                f"({source}) --[{relation_type}]--> ({target})"
            )

        # Return all graph insights as newline-separated text.
        return "\n".join(insights)