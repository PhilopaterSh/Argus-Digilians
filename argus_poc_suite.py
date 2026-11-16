"""Argus Usage PoC suite - 7 offline, deterministic component demos.

Every PoC imports the REAL framework code and exercises it against
simulated, zero-network inputs (no cloud, no live targets, no destructive
operations). Outputs printed here are the exact ones embedded in the
vault notes as the verified Usage PoC sections.
"""
import tempfile
from pathlib import Path

from app.core.registry.base_tool import BaseToolService, ToolMetadata
from app.core.registry.tool_registry import ToolRegistry
from app.core.memory.memory_service import ArgusMemory
from app.core.safety import SafetyLayer
from app.core.schemas import Finding, ScanMode, SecurityReport
from app.tools.path_traversal import PathTraversalScanner
from app.tools.reflective_verification import ReflectiveVerificationService

PASSWD_BODY = (
    "root:x:0:0:root:/root:/bin/bash\n"
    "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
    "philopater:x:1000:1000:Philopater Shenouda,,,:/home/philopater:/bin/bash\n"
)


class FakeRunner:
    """Offline stand-in for the WSL Kali CommandRunner: returns a canned
    /etc/passwd body for any probe command (the classic traversal proof)."""

    def __init__(self, body: str = PASSWD_BODY):
        self.body = body
        self.commands: list[str] = []

    def run(self, command, timeout=30):
        command = str(command)
        self.commands.append(command)
        if "--path-as-is" in command or "../../" in command or "/etc/passwd" in command:
            return self.body
        return "HTTP/1.1 200 OK"



def poc_registry():
    print("=" * 8, "POC 1 - Tool Registry (note 07)", "=" * 8)

    class WhoisLookup(BaseToolService):
        @property
        def metadata(self) -> ToolMetadata:
            return ToolMetadata(name="Whois_Lookup", description="Offline whois metadata lookup demo")

        def execute(self, **kwargs):
            return {"domain": kwargs.get("domain", "lab.local"), "registrar": "simulated"}

    reg = ToolRegistry()
    tool = WhoisLookup()
    reg.register(tool)
    reg.register(tool)  # duplicate registration -> parse-time validation gate
    names = reg.get_tool_names()
    meta = reg.get_tool("Whois_Lookup").metadata
    print("registered tools:", names)
    print("lookup metadata:", meta.name, "-", meta.description)
    print("execute:", tool.execute(domain="lab.local"))
    print("registry count:", len(reg.list_tools()))


def poc_safety():
    print("=" * 8, "POC 2 - Safety Layer (note 36)", "=" * 8)
    s = SafetyLayer()
    print("destructive 'rm -rf /'      ->", s.is_destructive_payload("rm -rf /"))
    print("destructive 'nmap -sV host' ->", s.is_destructive_payload("nmap -sV host"))
    ok, why = s.validate_target("https://lab.enterprise.internal", mode="passive")
    print("validate_target lab.local   ->", ok, "|", why)
    bad, why = s.validate_target("https://example.com", mode="passive")
    print("validate_target example.com ->", bad, "|", why)
    allowed, why = s.guard_command("cat /var/log/app.log")
    print("guard_command 'cat log'     ->", allowed, "|", why)


def poc_memory():
    print("=" * 8, "POC 3 - ArgusMemory Blackboard (note 06)", "=" * 8)
    db = Path(tempfile.mkdtemp(prefix="argus_poc_mem_")) / "blackboard.db"
    mem = ArgusMemory(str(db))
    host_id = mem.upsert_entity("host", "lab.enterprise.internal")
    svc_id = mem.upsert_entity("service", "Apache/2.4.49")
    mem.add_relation(host_id, svc_id, "runs", strength=0.9)
    mem.upsert_target("lab.enterprise.internal", priority=1)
    mem.add_finding("lab.enterprise.internal", "PathTraversalScanner", "attack_path",
                    "CVE-2021-41773 payload body (simulated)",
                    "Path traversal confirmed with content signature",
                    severity="High")
    print("graph insights:")
    print(mem.get_graph_insights())
    print("blackboard summary (first 220 chars):")
    print(mem.get_blackboard_summary(max_chars=220))


def poc_report():
    print("=" * 8, "POC 4 - Report Contract (note 38)", "=" * 8)
    report = SecurityReport(
        summary="Simulated passive assessment of the lab target - one confirmed traversal finding.",
        attack_surface_stats="1 host (lab.enterprise.internal); 1 service (Apache/2.4.49); 12 observed paths",
        findings=[
            Finding(
                target="lab.enterprise.internal",
                issue="Path Traversal exposing /etc/passwd (CVE-2021-41773 family)",
                severity="High",
                description="Encoded traversal payload returned a real passwd body; content-signature verification locked 3/3.",
                suggested_payload="curl --path-as-is http://lab.enterprise.internal/index.php?page=/etc/passwd",
                remediation="Upgrade Apache; reject encoded traversal sequences at the edge.",
                tool_source="PathTraversalScanner",
            )
        ],
        overall_risk_score=8,
        next_steps=[
            "Fingerprint the exact Apache build",
            "Test CVE-2021-42013 as the patched bypass",
            "Document remediation in the executive report",
        ],
        scan_mode=ScanMode.PASSIVE,
        scan_target="https://lab.enterprise.internal",
        output=None,
    )
    data = report.model_dump()
    print("scan_mode:", data["scan_mode"], "| findings:", len(data["findings"]), "| risk:", data["overall_risk_score"])
    f = data["findings"][0]
    print("finding[0]:", f["issue"], "| severity:", f["severity"], "| tool:", f["tool_source"])


def poc_reflective():
    print("=" * 8, "POC 5 - Reflective Verification (note 21)", "=" * 8)
    runner = FakeRunner()
    mem = ArgusMemory(str(Path(tempfile.mkdtemp(prefix="argus_poc_mem_")) / "blackboard.db"))
    svc = ReflectiveVerificationService(runner, mem)
    print("pre_execute_verify('nmap -sV lab.local'):")
    print("  ->", svc.pre_execute_verify("nmap -sV lab.local"))
    print("pre_execute_verify('rm -rf / --no-preserve-root'):")
    print("  ->", svc.pre_execute_verify("rm -rf / --no-preserve-root"))
    verdict = svc.post_execute_verify(
        "https://lab.enterprise.internal",
        "curl --path-as-is http://lab.enterprise.internal/index.php?page=/etc/passwd",
        PASSWD_BODY,
    )
    print("post_execute_verify (passwd body):")
    print("  ->", str(verdict)[:220])


def poc_path_traversal():
    print("=" * 8, "POC 6 - Path Traversal Scanner (note 44)", "=" * 8)
    runner = FakeRunner()
    mem = ArgusMemory(str(Path(tempfile.mkdtemp(prefix="argus_poc_mem_")) / "blackboard.db"))
    scanner = PathTraversalScanner(runner, mem)
    result = scanner.run_traversal_scan(
        "http://lab.enterprise.internal/index.php?page=", max_probes=3,
    )
    print("scan result (first 300 chars):")
    print(str(result)[:300])
    print("commands issued by the scanner:", len(runner.commands))


def poc_screenshot():
    print("=" * 8, "POC 7 - Screenshot Evidence (note 45)", "=" * 8)
    from app.tools.browser_manager import BrowserManager

    work = Path(tempfile.mkdtemp(prefix="argus_poc_shots_"))
    (work / "target.html").write_text(
        "<html><body><h1>Simulated lab target</h1>"
        "<p>Local evidence-capture fixture - zero network.</p></body></html>",
        encoding="utf-8",
    )
    target_url = work.joinpath("target.html").as_uri()
    mgr = BrowserManager(screenshot_dir=str(work), headless=True)
    mgr.start(target=target_url)
    print("started:", mgr.is_started, "| target:", mgr.target)
    shot = mgr.capture_site_context(target_url)
    print("capture_site_context ->", shot)
    mgr.close()
    print("closed:", not mgr.is_started)


if __name__ == "__main__":
    poc_registry()
    poc_safety()
    poc_memory()
    poc_report()
    poc_reflective()
    poc_path_traversal()
    poc_screenshot()
