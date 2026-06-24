import os
import json
import time
import random
from datetime import datetime
from app.core.memory.memory_service import ArgusMemory

class ZEROAPTSimulation:
    """
    Implements a three-party interactive simulation (Attacker, Defender, Judge)
    similar to the ZERO-APT benchmarking framework.
    """

    def __init__(self, runner, memory: ArgusMemory):
        self.runner = runner
        self.memory = memory

    def run_simulation(self, target_url: str, defense_level: str = "L2") -> str:
        """
        Runs the ZERO-APT simulation cycle.
        Defense Levels:
          - L1: Weak perception (Standard logs, high noise, slow response)
          - L2: SOC / Sigma rules (Process tracing, detects standard exploits)
          - L3: Active Adversary Tracking (Threat intelligence matching, aggressive blocking)
        """
        clean_target = target_url.replace("https://", "").replace("http://", "").split("/")[0]
        print(f"[*] Starting ZERO-APT Simulation against: {clean_target} (Defense: {defense_level})")
        
        # Attack Execution Lifecycle simulation
        steps = [
            {"phase": "Reconnaissance", "action": "subfinder -d target.com", "severity": "low"},
            {"phase": "Port Scan", "action": "nmap -sV -T4 target.com", "severity": "low"},
            {"phase": "Vulnerability Scan", "action": "nikto -h target.com", "severity": "medium"},
            {"phase": "Directory Brute Force", "action": "ffuf -w wordlist.txt -u target.com/FUZZ", "severity": "medium"},
            {"phase": "Exploit Delivery", "action": "curl -X POST -d 'payload' target.com/upload.php", "severity": "high"},
            {"phase": "Privilege Escalation", "action": "sudo -l && dirty_pipe_exploit", "severity": "critical"}
        ]

        attacker_log = []
        defender_log = []
        judge_log = []
        
        defender_points = 0
        attacker_points = 0
        
        # SIMULATION LOOP
        for step in steps:
            phase = step["phase"]
            action = step["action"].replace("target.com", clean_target)
            severity = step["severity"]
            
            attacker_log.append(f"[{phase}] Attacker executes: `{action}`")
            
            # Defender reaction based on level
            detected = False
            response_action = "Logged event."
            
            if defense_level == "L1":
                # L1 only detects high/critical actions with 50% probability
                if severity in ["high", "critical"] and random.random() > 0.5:
                    detected = True
                    response_action = "Triggered generic alert."
                    defender_points += 10
                else:
                    attacker_points += 20
            
            elif defense_level == "L2":
                # L2 (SOC / Sigma rules) detects medium/high/critical with high probability
                if severity in ["medium", "high", "critical"]:
                    detected = True
                    if severity == "medium":
                        response_action = "Sigma Alert: Suspicious HTTP scanner patterns detected."
                        defender_points += 15
                    elif severity == "high":
                        response_action = "Sigma Alert: Web shell upload attempt blocked by WAF rule #941100."
                        defender_points += 25
                    elif severity == "critical":
                        response_action = "Sysmon Alert: Child process spawned by lsass.exe. Process terminated."
                        defender_points += 35
                attacker_points += 10
                
            elif defense_level == "L3":
                # L3 (Advanced Hunting) detects almost everything and adapts
                detected = True
                if severity == "low":
                    response_action = "Threat Intel Alert: Quiet port scan matching APT IP subnet detected. Adding IP to blacklist."
                    defender_points += 20
                elif severity == "medium":
                    response_action = "Firewall Rule: Aggressive directory fuzzing detected. Blacklisted source IP."
                    defender_points += 30
                elif severity == "high":
                    response_action = "WAF Bypass Countermeasure: Dynamic decoy response (honeypot) injected."
                    defender_points += 40
                elif severity == "critical":
                    response_action = "SOC Host Containment: Host isolated immediately. Session closed."
                    defender_points += 50
                attacker_points += 5

            state_desc = "DETECTED" if detected else "PASSED"
            defender_log.append(f"[{phase}] Defender status: {state_desc} - {response_action}")
            
            # Judge Verdict
            verdict = ""
            if detected:
                verdict = f"Judge: Defender successfully recognized and mitigated '{phase}' action."
            else:
                verdict = f"Judge: Attacker successfully bypassed defense on '{phase}' phase."
            judge_log.append(verdict)
            
            # Check if attack is completely blocked (L3 kills it early)
            if defense_level == "L3" and severity in ["medium", "high"]:
                judge_log.append("Judge: Attacker IP blacklisted. Attack aborted.")
                break
            if defense_level == "L2" and severity == "high":
                judge_log.append("Judge: Exploit blocked by WAF. Attacker needs to pivot.")
                break

        # Calculate final results
        winner = "Attacker" if attacker_points > defender_points else "Defender"
        if defender_points >= 75:
            winner = "Defender (Defensive Threshold Exceeded)"

        # STIX 2.0 Report Generation
        stix_report = {
            "type": "bundle",
            "id": f"bundle--{random.randint(1000, 9999)}",
            "spec_version": "2.0",
            "objects": [
                {
                    "type": "identity",
                    "id": f"identity--{random.randint(1000, 9999)}",
                    "name": "Argus AI Attacker Agent"
                },
                {
                    "type": "identity",
                    "id": f"identity--{random.randint(1000, 9999)}",
                    "name": f"Adversary Target: {clean_target}"
                },
                {
                    "type": "attack-pattern",
                    "id": f"attack-pattern--{random.randint(1000, 9999)}",
                    "name": "Multi-Agent Simulation Attack Pattern",
                    "description": f"Simulation run with defense level {defense_level}"
                },
                {
                    "type": "observed-data",
                    "id": f"observed-data--{random.randint(1000, 9999)}",
                    "first_observed": datetime.now().isoformat(),
                    "last_observed": datetime.now().isoformat(),
                    "number_of_observed_data": len(attacker_log),
                    "objects": {
                        "0": {
                            "type": "software",
                            "name": "Kali Security Tools"
                        }
                    }
                },
                {
                    "type": "report",
                    "id": f"report--{random.randint(1000, 9999)}",
                    "name": "ZERO-APT Performance Report",
                    "description": f"Overall Winner: {winner}. Attacker Score: {attacker_points}, Defender Score: {defender_points}.",
                    "published": datetime.now().isoformat(),
                    "object_refs": []
                }
            ]
        }
        
        # Save to reports folder
        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/zero_apt_simulation_{clean_target}_{defense_level}_{int(time.time())}.json"
        with open(report_path, "w") as f:
            json.dump(stix_report, f, indent=4)

        # Build output message
        summary = [
            f"=== ZERO-APT CLOSED-LOOP SIMULATION REPORT ===",
            f"Target: {clean_target}",
            f"Defense Posture: {defense_level}",
            f"Attacker Score: {attacker_points} | Defender Score: {defender_points}",
            f"Verdict: {winner}",
            f"STIX 2.0 Report Location: {report_path}",
            "\n--- ATTACKER TIMELINE ---"
        ] + attacker_log + ["\n--- DEFENDER TELEMETRY ---"] + defender_log + ["\n--- JUDGE VERDICTS ---"] + judge_log
        
        # Add to memory
        self.memory.add_finding(clean_target, "zero_apt_simulation", "simulation_run", f"Defense {defense_level}", f"Verdict: {winner}")
        
        return "\n".join(summary)
