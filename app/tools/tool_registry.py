import os
from app.core.memory.memory_service import ArgusMemory
from app.tools.wsl_bridge import WSLBridge, WSLConfig
from app.tools.command_runner import CommandRunner
from app.tools.recon import ReconService
from app.tools.scanners import VulnerabilityScanners
from app.tools.payloads import PayloadSuggester
from app.tools.secrets import SecretAnalyzer
from app.tools.web_search import SmartWebSearch
from app.tools.reachability import ReachabilityService, JSONReportWriter
from app.tools.crawler import CrawlerService
from app.tools.evasion import EvasionService
from app.tools.self_heal import SelfHealingService

class WSLBridgeTools:
    """
    Facade that preserves the original public API from tools.py.
    Internally, it delegates each responsibility to a focused service class.
    """

    def __init__(self):
        self.memory = ArgusMemory()
        self.bridge = WSLBridge(WSLConfig())
        self.runner = CommandRunner(self.bridge)
        
        self.report_writer = JSONReportWriter()
        self.recon = ReconService(
            runner=self.runner,
            memory=self.memory,
            report_writer=self.report_writer
        )
        self.scanners = VulnerabilityScanners(self.runner, self.memory)
        self.payloads = PayloadSuggester(self.runner)
        self.secrets = SecretAnalyzer(self.runner, self.memory)
        self.web = SmartWebSearch(self.memory)
        self.reachability = ReachabilityService(self.runner, self.memory)
        self.crawler = CrawlerService(self.runner, self.memory)
        self.evasion = EvasionService(self.runner, self.memory)
        self.self_heal = SelfHealingService(self.runner)

    # Legacy Properties for compatibility
    @property
    def host(self): return self.bridge.config.host
    @property
    def distro(self): return self.bridge.config.distro
    @property
    def user(self): return self.bridge.config.user
    @property
    def last_recon_results(self): return self.recon.last_recon_results

    # Delegated Methods
    def run(self, command, show_prompt=False):
        return self.runner.run(command, show_prompt)

    def check_reachability(self, domain):
        return self.reachability.check_reachability(domain)

    def recon_suite(self, url, selected_targets=None):
        return self.recon.recon_suite(url, selected_targets)

    def enumerate_subdomains(self, domain):
        return self.recon.enumerate_subdomains(domain)

    def prioritize_targets(self, targets):
        return self.recon.prioritize_targets(targets)

    def run_nikto(self, url):
        return self.scanners.run_nikto(url)

    def run_ffuf_discovery(self, url):
        return self.scanners.run_ffuf_discovery(url)

    def suggest_payloads(self, vulnerability_type):
        return self.payloads.suggest_payloads(vulnerability_type)

    def analyze_secrets(self, url):
        return self.secrets.analyze_secrets(url)

    def smart_web_search(self, query):
        return self.web.smart_web_search(query)

    def archive_research_subagent(self, query):
        return self.web.archive_research_subagent(query)

    def crawl_target(self, url):
        return self.crawler.crawl_target(url)

    def advanced_vuln_probe(self, url):
        return self.evasion.advanced_vuln_probe(url)

    def system_self_heal(self, tool_info):
        return self.self_heal.system_self_heal(tool_info)

    def get_intelligence_summary(self, _=None):
        return self.memory.get_blackboard_summary()

    def query_knowledge_graph(self, _=None):
        return self.memory.get_graph_insights()

    def run_kali_command(self, command):
        """Proxy for manual command execution in Kali."""
        # Ensure Go bins are in PATH for the command execution
        full_command = f"export PATH=$PATH:/home/kali/go/bin:/home/kali/.pdtm/go/bin && {command}"
        return self.runner.run(full_command, show_prompt=True)
