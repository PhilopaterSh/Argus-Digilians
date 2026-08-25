"""Tool-wiring facade: imports every concrete tool service and registers
instances into a `ToolRegistry`.

Note the sibling `app/core/registry/tool_registry.py` - same basename,
different module: that file defines the generic `ToolRegistry` class
(imported below); this file is `WSLBridgeTools`, the facade that owns and
populates one. If disambiguating by basename alone, check the full import
path.
"""
import logging
from typing import Any

from app.core.memory.memory_service import ArgusMemory
from app.core.registry.base_tool import BaseToolService, ToolMetadata
from app.core.registry.tool_registry import ToolRegistry
from app.tools.wsl_bridge import WSLBridge, WSLConfig
from app.tools.command_runner import CommandRunner
from app.tools.recon import ReconService
from app.tools.scanners import VulnerabilityScanners
from app.tools.path_traversal import PathTraversalScanner
from app.tools.payloads import PayloadSuggester
from app.tools.secrets import SecretAnalyzer
from app.tools.web_search import SmartWebSearch
from app.tools.reachability import ReachabilityService, JSONReportWriter
from app.tools.crawler import CrawlerService
from app.tools.evasion import EvasionService
from app.tools.path_traversal import PathTraversalScanner
from app.tools.browser_manager import BrowserManager
from app.tools.self_heal import SelfHealingService
from app.tools.reflective_verification import ReflectiveVerificationService

logger = logging.getLogger(__name__)


class _ToolServiceAdapter(BaseToolService):
    """Wraps a legacy tool service as a BaseToolService-compatible adapter."""

    def __init__(self, name: str, description: str, service, method_name: str):
        """Wrap one method of a legacy tool service as a callable tool.

        Args:
            name (str): Tool name to register under.
            description (str): Human-readable tool description.
            service: The legacy service instance owning the method.
            method_name (str): Name of the method on `service` to call
                when `execute()` is invoked.
        """
        self._meta = ToolMetadata(name=name, description=description)
        self._service = service
        self._method_name = method_name

    @property
    def metadata(self) -> ToolMetadata:
        """Metadata."""
        return self._meta

    def execute(self, **kwargs) -> Any:
        """Call the wrapped service's method with the given keyword arguments.

        Args:
            **kwargs: Forwarded as keyword arguments to the wrapped method.

        Returns:
            Any: Whatever the wrapped method returns.
        """
        method = getattr(self._service, self._method_name)
        return method(**kwargs)


class WSLBridgeTools:
    """
    Facade that preserves the original public API from tools.py.
    Internally, it delegates each responsibility to a focused service class.
    Uses ToolRegistry for tool discovery and dispatch.
    """

    def __init__(self):
        """Construct every concrete tool service and register their
        adapters into a fresh ToolRegistry."""
        self.memory = ArgusMemory()
        self.bridge = WSLBridge(WSLConfig())
        self.runner = CommandRunner(self.bridge)

        self.registry = ToolRegistry()

        self.report_writer = JSONReportWriter()
        self.recon = ReconService(
            runner=self.runner,
            memory=self.memory,
            report_writer=self.report_writer
        )
        self.scanners = VulnerabilityScanners(self.runner, self.memory)
        self.path_traversal = PathTraversalScanner(self.runner, self.memory)
        self.payloads = PayloadSuggester(self.runner)
        self.secrets = SecretAnalyzer(self.runner, self.memory)
        self.web = SmartWebSearch(self.memory)
        self.reachability = ReachabilityService(self.runner, self.memory)
        self.crawler = CrawlerService(self.runner, self.memory)
        # specs/029: persistent, host-side (no Kali/SSH involvement) browser
        # session - opened lazily on first use, stays open for the whole
        # test run, closed via close_browser() (wired into
        # scripts/run_agent.py's run_brain_analysis() finally block).
        self.browser_manager = BrowserManager()
        self.evasion = EvasionService(self.runner, self.memory, browser_manager=self.browser_manager)
        # The dedicated scanner existed and was fully tested, but was never
        # registered here - so nothing in the pipeline could ever call it.
        self.path_traversal = PathTraversalScanner(self.runner, self.memory)
        self.self_heal = SelfHealingService(self.runner)
        self.verifier = ReflectiveVerificationService(self.runner, self.memory)

        self._register_defaults()

    def _register_defaults(self):
        """Register one _ToolServiceAdapter per tool method onto self.registry."""
        self.registry.register(_ToolServiceAdapter(
            "recon", "Execute advanced reconnaissance suite", self.recon, "recon_suite"
        ))
        self.registry.register(_ToolServiceAdapter(
            "subdomains", "Enumerate subdomains", self.recon, "enumerate_subdomains"
        ))
        self.registry.register(_ToolServiceAdapter(
            "reachability", "Check target reachability", self.reachability, "check_reachability"
        ))
        self.registry.register(_ToolServiceAdapter(
            "nikto", "Run Nikto vulnerability scanner", self.scanners, "run_nikto"
        ))
        self.registry.register(_ToolServiceAdapter(
            "ffuf", "Run FFUF for path discovery", self.scanners, "run_ffuf_discovery"
        ))
        self.registry.register(_ToolServiceAdapter(
            "path_traversal", "Dedicated path-traversal / LFI probe (multi-encoding, hybrid param discovery)",
            self.path_traversal, "run_traversal_scan"
        ))
        self.registry.register(_ToolServiceAdapter(
            "payloads", "Suggest exploit payloads", self.payloads, "suggest_payloads"
        ))
        self.registry.register(_ToolServiceAdapter(
            "secrets", "Analyze secrets in responses", self.secrets, "analyze_secrets"
        ))
        self.registry.register(_ToolServiceAdapter(
            "web_search", "Smart web search for OSINT", self.web, "smart_web_search"
        ))
        self.registry.register(_ToolServiceAdapter(
            "archive_search", "Archive research subagent", self.web, "archive_research_subagent"
        ))
        self.registry.register(_ToolServiceAdapter(
            "crawler", "Crawl target URLs", self.crawler, "crawl_target"
        ))
        self.registry.register(_ToolServiceAdapter(
            "evasion", "Advanced vulnerability probe with evasion", self.evasion, "advanced_vuln_probe"
        ))
        self.registry.register(_ToolServiceAdapter(
            "path_traversal", "Dedicated multi-encoding path traversal scan",
            self.path_traversal, "run_traversal_scan"
        ))
        self.registry.register(_ToolServiceAdapter(
            "capture_screenshot", "Capture a screenshot of a URL as vulnerability evidence",
            self.browser_manager, "capture_vulnerability"
        ))
        self.registry.register(_ToolServiceAdapter(
            "self_heal", "Autonomously install missing tools", self.self_heal, "system_self_heal"
        ))
        self.registry.register(_ToolServiceAdapter(
            "verify_command", "Validate command syntax and detect infinite loops", self.verifier, "pre_execute_verify"
        ))
        self.registry.register(_ToolServiceAdapter(
            "verify_output", "Analyze command output for WAF blocks and false positives", self.verifier, "post_execute_verify"
        ))
        self.registry.register(_ToolServiceAdapter(
            "assess_difficulty", "Task Difficulty Assessment for target selection", self.verifier, "task_difficulty_assessment"
        ))
        self.registry.register(_ToolServiceAdapter(
            "intelligence", "Query blackboard intelligence summary", self.memory, "get_blackboard_summary"
        ))
        self.registry.register(_ToolServiceAdapter(
            "knowledge_graph", "Query knowledge graph insights", self.memory, "get_graph_insights"
        ))
        logger.info("Registered %d tools in registry", len(self.registry))

    # Legacy Properties for compatibility
    @property
    def host(self):
        """The configured WSL/SSH host, delegated from self.bridge."""
        return self.bridge.config.host
    @property
    def distro(self):
        """The configured WSL distro name, delegated from self.bridge."""
        return self.bridge.config.distro
    @property
    def user(self):
        """The configured WSL/SSH user, delegated from self.bridge."""
        return self.bridge.config.user
    @property
    def last_recon_results(self):
        """The most recent recon_suite() results dict, delegated from self.recon."""
        return self.recon.last_recon_results

    # Delegated Methods
    def run(self, command, show_prompt=False):
        """Delegate to CommandRunner.run() - see that method's docstring."""
        return self.runner.run(command, show_prompt)

    def check_reachability(self, domain):
        """Delegate to ReachabilityService.check_reachability()."""
        return self.reachability.check_reachability(domain)

    def recon_suite(self, url, selected_targets=None):
        """Delegate to ReconService.recon_suite() - see that method's docstring."""
        return self.recon.recon_suite(url, selected_targets)

    def enumerate_subdomains(self, domain):
        """Delegate to ReconService.enumerate_subdomains()."""
        return self.recon.enumerate_subdomains(domain)

    def prioritize_targets(self, targets):
        """Delegate to ReconService.prioritize_targets()."""
        return self.recon.prioritize_targets(targets)

    def run_nikto(self, url):
        """Delegate to VulnerabilityScanners.run_nikto()."""
        return self.scanners.run_nikto(url)

    def run_ffuf_discovery(self, url):
        """Delegate to VulnerabilityScanners.run_ffuf_discovery()."""
        return self.scanners.run_ffuf_discovery(url)

    def run_traversal_scan(self, url, params=None, max_probes=60):
        return self.path_traversal.run_traversal_scan(url, params=params, max_probes=max_probes)

    def suggest_payloads(self, vulnerability_type):
        """Delegate to PayloadSuggester.suggest_payloads()."""
        return self.payloads.suggest_payloads(vulnerability_type)

    def analyze_secrets(self, url):
        """Delegate to SecretAnalyzer.analyze_secrets()."""
        return self.secrets.analyze_secrets(url)

    def smart_web_search(self, query):
        """Delegate to SmartWebSearch.smart_web_search()."""
        return self.web.smart_web_search(query)

    def archive_research_subagent(self, query):
        """Delegate to SmartWebSearch.archive_research_subagent()."""
        return self.web.archive_research_subagent(query)

    def crawl_target(self, url):
        """Delegate to CrawlerService.crawl_target()."""
        return self.crawler.crawl_target(url)

    def advanced_vuln_probe(self, url):
        """Delegate to EvasionService.advanced_vuln_probe()."""
        return self.evasion.advanced_vuln_probe(url)

    def run_traversal_scan(self, url):
        """Delegate to PathTraversalScanner.run_traversal_scan()."""
        return self.path_traversal.run_traversal_scan(url)

    def capture_vulnerability_screenshot(self, url, vulnerability_type="path_traversal", payload=None, note=None):
        """On-demand evidence capture (specs/029) - separate from the
        automatic capture already wired into advanced_vuln_probe(), for
        when the agent/operator wants a screenshot of a specific URL
        outside that flow."""
        return self.browser_manager.capture_vulnerability(vulnerability_type, url, payload=payload, note=note)

    def close_browser(self):
        """Ends the persistent BrowserManager session (specs/029) - call
        once the whole test run is finished. Idempotent."""
        self.browser_manager.close()

    def system_self_heal(self, tool_info):
        """Delegate to SelfHealingService.system_self_heal()."""
        return self.self_heal.system_self_heal(tool_info)

    def verify_command(self, command):
        """Verify command."""
        return self.verifier.pre_execute_verify(command)

    def verify_output(self, url, command, raw_output):
        """Verify output."""
        return self.verifier.post_execute_verify(url, command, raw_output)

    def assess_difficulty(self, targets):
        """Assess difficulty."""
        return self.verifier.task_difficulty_assessment(targets)

    def get_intelligence_summary(self, _=None):
        """Delegate to ArgusMemory.get_blackboard_summary(). `_` is accepted
        and ignored for call-site compatibility."""
        return self.memory.get_blackboard_summary()

    def query_knowledge_graph(self, _=None):
        """Delegate to ArgusMemory.get_graph_insights(). `_` is accepted
        and ignored for call-site compatibility."""
        return self.memory.get_graph_insights()

    def run_kali_command(self, command):
        """Proxy for manual command execution in Kali.

        Args:
            command (str): The shell command to run, with Go tool-install
                bin directories prepended to PATH.

        Returns:
            str: The command's output, per CommandRunner.run() (with
            `show_prompt=True`, so it's prefixed with a fake shell prompt).
        """
        # Ensure Go bins are in PATH for the command execution
        full_command = f"export PATH=$PATH:/home/kali/go/bin:/home/kali/.pdtm/go/bin && {command}"
        return self.runner.run(full_command, show_prompt=True)
