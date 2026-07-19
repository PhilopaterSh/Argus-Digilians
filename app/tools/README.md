app/tools/ — Tool service layer

Purpose:
This folder contains focused service classes that run recon, scanning, payload suggestion, crawling, evasion, reflective verification, and the WSL/SSH command bridge.

Public API:
- tool_registry.WSLBridgeTools: Facade exposing commonly used methods (recon_suite, run_nikto, run_ffuf_discovery, etc.).
- command_runner.CommandRunner: Executes commands through WSL or SSH with output cleaning and WAF detection.

Conventions:
- Keep each service single-responsibility.
- Avoid shelling out without sanitizing inputs. Unit-test CommandRunner edge cases.