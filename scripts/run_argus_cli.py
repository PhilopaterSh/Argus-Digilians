import os
import sys
import argparse
import datetime
import pathlib

# Ensure the project root is on the import path before importing app modules.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.tools.tool_registry import WSLBridgeTools
from app.core.agent.brain import ArgusBrain
from app.core.agent.brain_tools import build_argus_tools
from app.core.config import ArgusConfig
from dotenv import load_dotenv

load_dotenv()
config = ArgusConfig.load()

# Some lower-level dependency opens websocket connections without explicit
# ping settings, causing spurious keepalive timeouts (close code 1011).
# Patch forgiving defaults; fall back silently if websockets isn't installed
# or its internal API changes.
try:
    from websockets.legacy.protocol import WebSocketCommonProtocol
    _orig_ws_init = WebSocketCommonProtocol.__init__

    def _patched_ws_init(self, *args, **kwargs):
        kwargs.setdefault("ping_interval", 30)
        kwargs.setdefault("ping_timeout", 60)
        pi = kwargs.get("ping_interval")
        pt = kwargs.get("ping_timeout")
        if pi is not None and isinstance(pi, (int, float)) and pi < 5:
            kwargs["ping_interval"] = 30
        if pt is not None and isinstance(pt, (int, float)) and pt < 10:
            kwargs["ping_timeout"] = 60
        return _orig_ws_init(self, *args, **kwargs)

    WebSocketCommonProtocol.__init__ = _patched_ws_init
except Exception:
    pass


def _sanitize_filename(s: str) -> str:
    return ''.join(c for c in s if c.isalnum() or c in '-_.').rstrip()


def _write_progress(target_url: str, message: str):
    try:
        reports_dir = pathlib.Path(PROJECT_ROOT) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        safe_name = _sanitize_filename(target_url.replace('https://', '').replace('http://', '').replace('/', '_'))
        path = reports_dir / f"{safe_name}_progress.log"
        timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        with path.open('a', encoding='utf-8') as fh:
            fh.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def run_analysis(target_url):
    bridge = WSLBridgeTools()
    model = config.model_name

    # specs/018 CHK090: this used to hand-maintain its own 13-tool list,
    # independently drifted from app/core/agent/brain_tools.py's supposedly
    # "canonical" one (4 tools existed only here: Crawl_Target,
    # Advanced_Evasion_Probe, Reflective_Pre_Verify, Task_Difficulty_Assessment
    # - now merged into the real canonical list, which this imports instead
    # of re-declaring). A "Reflective_Post_Verify" tool (bridge.verify_output)
    # was considered but dropped from the canonical list too - it requires 3
    # positional args (url, command, raw_output), which a single-string
    # LangChain Tool cannot supply.
    tools = build_argus_tools(bridge)

    brain = ArgusBrain(model, tools)

    print(f"\n[!] ARGUS CLI MODE ACTIVATED")
    print(f"[*] Target: {target_url}")
    print(f"[*] Model: {model}")
    print("[*] Initializing autonomous security reasoning...\n")
    print("-" * 60)

    try:
        _write_progress(target_url, 'CLI started')
        query = f"Perform a comprehensive security analysis for {target_url}. Start with reachability, then map the attack surface, and finally provide a deep risk assessment."
        _write_progress(target_url, 'Preparing AI agent')

        reach = bridge.check_reachability(target_url)
        _write_progress(target_url, f'Reachability: {str(reach)[:800]}')

        # Brain.ask returns a dict with "output" (parsed JSON) or raw result
        _write_progress(target_url, 'Starting main brain.ask analysis')
        result = brain.ask(query)
        _write_progress(target_url, 'AI analysis complete')

        print("\n" + "="*60)
        print("[REPORT] ARGUS AGENT FINAL REPORT")
        print("="*60)

        if isinstance(result, dict) and "output" in result:
            output = result["output"]
            if isinstance(output, dict):
                import json
                print(json.dumps(output, indent=4))
            else:
                print(output)
        else:
            print(result)

        _write_progress(target_url, 'Completed')
    except KeyboardInterrupt:
        _write_progress(target_url, 'Interrupted by user')
        print("\n[!] Analysis interrupted by user.")
    except Exception as e:
        _write_progress(target_url, f'Error: {e}')
        print(f"\n[!] An error occurred during execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Argus AI CLI")
    parser.add_argument("target", nargs="?", default="https://cultbeauty.co.uk/", help="Target URL")
    args = parser.parse_args()
    run_analysis(args.target)


