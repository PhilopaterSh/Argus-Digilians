"""Per-scan blackboard isolation.

`archive_and_reset_db()` runs once at the start of every scan process
(`scripts/run_agent.py`, `scripts/run_argus_cli.py`) so a scan cannot inherit
findings from previous runs. This matters most for crawler `link` findings:
`PathTraversalScanner` reads them back as tier-0 injection points with no
recency filter, so a stale blackboard made the same target report vulnerable
on one run and clean on the next.
"""
import os
import sqlite3

import pytest

from app.core.memory.memory_service import ArgusMemory, archive_and_reset_db

pytestmark = pytest.mark.unit


@pytest.fixture
def db_path(tmp_path):
    """Return a path for an isolated Blackboard DB inside a temp dir.

    Args:
        tmp_path: pytest fixture providing a unique temporary directory.

    Returns:
        str: Path to a not-yet-created SQLite database.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return str(data_dir / "argus_intelligence.db")


def _seed(db_path, host, links=2):
    """Populate `db_path` with a target and some crawler link findings.

    Args:
        db_path (str): Blackboard DB path.
        host (str): Target domain to record findings against.
        links (int): How many `link`-typed findings to add.

    Returns:
        ArgusMemory: The memory instance used to seed.
    """
    mem = ArgusMemory(db_path)
    mem.upsert_target(host)
    for i in range(links):
        mem.add_finding(host, "crawler", "link", f"/product?productId={i}", "crawled")
    return mem


def _counts(db_path):
    """Return `(targets, findings)` row counts for `db_path`.

    Args:
        db_path (str): Blackboard DB path.

    Returns:
        tuple[int, int]: Number of target and finding rows.
    """
    conn = sqlite3.connect(db_path)
    try:
        return (
            conn.execute("SELECT COUNT(*) FROM targets").fetchone()[0],
            conn.execute("SELECT COUNT(*) FROM findings").fetchone()[0],
        )
    finally:
        conn.close()


class TestArchiveAndReset:
    def test_reset_leaves_an_empty_blackboard(self, db_path):
        """A scan starting after a reset must see none of the prior scan.

        Args:
            db_path: Fixture-provided Blackboard DB path.
        """
        _seed(db_path, "scan1.example.com")
        assert _counts(db_path) == (1, 2)

        archive_and_reset_db(db_path)
        ArgusMemory(db_path)

        assert _counts(db_path) == (0, 0)

    def test_previous_scan_is_recoverable_from_the_archive(self, db_path):
        """Wiping must never destroy data - the archive has to be readable.

        Args:
            db_path: Fixture-provided Blackboard DB path.
        """
        _seed(db_path, "scan1.example.com")

        archived = archive_and_reset_db(db_path)

        assert archived and os.path.exists(archived)
        assert _counts(archived) == (1, 2)

    def test_wal_sidecars_move_with_the_database(self, db_path):
        """SQLite runs in WAL mode, so the DB is three files. Leaving a
        populated -wal behind would let the wiped rows come straight back.

        Args:
            db_path: Fixture-provided Blackboard DB path.
        """
        _seed(db_path, "scan1.example.com")
        for suffix in ("-wal", "-shm"):
            with open(db_path + suffix, "wb") as fh:
                fh.write(b"\x00" * 128)

        archived = archive_and_reset_db(db_path)

        for suffix in ("-wal", "-shm"):
            assert not os.path.exists(db_path + suffix), f"{suffix} left behind"
            assert os.path.exists(archived + suffix), f"{suffix} not archived"

    def test_crawler_links_do_not_leak_into_the_next_scan(self, db_path):
        """The concrete regression: PathTraversalScanner must not recover
        injection points from a previous scan's crawl.

        Args:
            db_path: Fixture-provided Blackboard DB path.

        Returns:
            None: The assertions inside the test carry the outcome.
        """
        from app.tools.path_traversal import PathTraversalScanner

        host = "lab.example.com"
        _seed(db_path, host, links=5)

        class Unreachable:
            """Every fetch fails, so any tier-0 point must come from the DB."""

            def run(self, command, timeout=None):
                """Execute nothing.

                Args:
                    command (str): Ignored probe command.
                    timeout (float | None): Ignored.

                Returns:
                    str: Always ``""``.
                """
                return ""

        def observed_points():
            """Return tier-0 injection points recoverable from memory alone.

            Returns:
                list[tuple[str, str]]: `(request_url, param)` pairs.
            """
            svc = PathTraversalScanner(Unreachable(), ArgusMemory(db_path))
            return [
                (u, p)
                for u, p, tier in svc._discover_injection_points_tiered(f"https://{host}/", None)
                if tier == 0
            ]

        assert observed_points(), "test setup: stale links should be reachable before reset"

        archive_and_reset_db(db_path)
        ArgusMemory(db_path)

        assert observed_points() == [], "previous scan's crawl leaked into the next scan"

    def test_keep_memory_env_var_opts_out(self, db_path, monkeypatch):
        """Chained-scan workflows need a way to keep accumulating.

        Args:
            db_path: Fixture-provided Blackboard DB path.
            monkeypatch: pytest fixture for setting the environment variable.
        """
        _seed(db_path, "scan1.example.com")
        monkeypatch.setenv("ARGUS_KEEP_MEMORY", "1")

        assert archive_and_reset_db(db_path) is None
        assert _counts(db_path) == (1, 2)

    def test_missing_database_is_a_no_op(self, db_path):
        """A first-ever run has nothing to archive and must not error.

        Args:
            db_path: Fixture-provided Blackboard DB path.
        """
        assert archive_and_reset_db(db_path) is None

    def test_archives_are_pruned_to_the_keep_limit(self, db_path):
        """Archives accumulate ~600 KB per run; retention must be bounded.

        Args:
            db_path: Fixture-provided Blackboard DB path.
        """
        archive_dir = os.path.join(os.path.dirname(db_path), "archive")
        for i in range(5):
            _seed(db_path, f"scan{i}.example.com")
            # Distinct stamps without sleeping: reset, then rename to a
            # deterministic timestamp so ordering is unambiguous.
            archived = archive_and_reset_db(db_path, keep=100)
            os.rename(archived, os.path.join(archive_dir, f"argus_intelligence_2026010{i}_000000.db"))

        _seed(db_path, "final.example.com")
        archive_and_reset_db(db_path, keep=3)

        kept = [f for f in os.listdir(archive_dir) if f.endswith(".db")]
        assert len(kept) == 3, f"expected 3 archives, found {len(kept)}: {sorted(kept)}"
