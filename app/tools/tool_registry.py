from core.memory import ArgusMemory
from tools.command_runner import CommandRunner
from tools.fuzzing import SensitiveFileFuzzer
from tools.payloads import PayloadSuggester
from tools.reachability import ReachabilityService
from tools.recon import ReconService
from tools.report_writer import JSONReportWriter
from tools.scanners import VulnerabilityScanners
from tools.secrets import SecretAnalyzer
from tools.web_search import SmartWebSearch
from tools.wsl_bridge import WSLBridge, WSLConfig


class WSLBridgeTools:
    """
    Facade that preserves the original public API from tools.py.

    Internally, it delegates each responsibility to a focused service class.
    """

    def __init__(self):
        self.memory = ArgusMemory()
        self.bridge = WSLBridge(WSLConfig())
        self.runner = CommandRunner(self.bridge)

        self.fuzzer = SensitiveFileFuzzer(self.runner)
        self.secret_analyzer = SecretAnalyzer(self.runner, self.memory)
        self.report_writer = JSONReportWriter()
        self.recon = ReconService(
            runner=self.runner,
            memory=self.memory,
            fuzzer=self.fuzzer,
            secret_analyzer=self.secret_analyzer,
            report_writer=self.report_writer,
        )
        self.reachability = ReachabilityService(self.runner, self.memory)
        self.scanners = VulnerabilityScanners(self.runner, self.memory)
        self.payloads = PayloadSuggester(self.runner)
        self.web = SmartWebSearch(self.memory)

    @property
    def host(self):
        return self.bridge.config.host

    @property
    def user(self):
        return self.bridge.config.user

    @property
    def password(self):
        return self.bridge.config.password

    @property
    def port(self):
        return self.bridge.config.port

    @property
    def distro(self):
        return self.bridge.config.distro

    @property
    def last_recon_results(self):
        return self.recon.last_recon_results

    def run(self, command, show_prompt=False):
        return self.runner.run(command, show_prompt)

    def check_reachability(self, domain):
        return self.reachability.check_reachability(domain)

    def fuzz_sensitive_files(self, url):
        return self.fuzzer.fuzz_sensitive_files(url)

    def analyze_secrets(self, url):
        return self.secret_analyzer.analyze_secrets(url)

    def recon_suite(self, url, selected_targets=None):
        return self.recon.recon_suite(url, selected_targets)

    def prioritize_targets(self, targets):
        return self.recon.prioritize_targets(targets)

    def enumerate_subdomains(self, domain):
        return self.recon.enumerate_subdomains(domain)

    def save_json_report(self, domain, data):
        return self.report_writer.save_json_report(domain, data)

    def get_intelligence_summary(self, _=None):
        return self.memory.get_blackboard_summary()

    def query_knowledge_graph(self, _=None):
        print("[*] Querying Knowledge Graph for cross-target insights...")
        return self.memory.get_graph_insights()

    def suggest_payloads(self, vulnerability_type):
        return self.payloads.suggest_payloads(vulnerability_type)

    def smart_web_search(self, query):
        return self.web.smart_web_search(query)

    def run_nikto(self, url):
        return self.scanners.run_nikto(url)

    def run_ffuf_discovery(self, url):
        return self.scanners.run_ffuf_discovery(url)
