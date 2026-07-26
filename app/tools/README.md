app/tools/ — Tool service layer

Purpose:
This folder contains focused service classes that run recon, scanning, payload suggestion, crawling, evasion, reflective verification, and the WSL/SSH command bridge.

Public API:
- tool_registry.WSLBridgeTools: Facade exposing commonly used methods (recon_suite, run_nikto, run_ffuf_discovery, run_traversal_scan, etc.).
- command_runner.CommandRunner: Executes commands through WSL or SSH with output cleaning and WAF detection.
- path_traversal.PathTraversalScanner: Dedicated path-traversal / LFI probe. Applies a multi-encoding matrix (raw, single/double URL-encoding, UTF-8 overlong, backslash, `....//` collapse) across depths 1..8, over hybrid-discovered parameters (crawler-derived from memory, then a static candidate fallback). Verifies via content signatures (SENSITIVE_CONTENT_INDICATORS), never HTTP status alone. Registered as the `path_traversal` tool and routed from exploit_node when the scanner selects that payload class.

Conventions:
- Keep each service single-responsibility.
- Avoid shelling out without sanitizing inputs. Unit-test CommandRunner edge cases.