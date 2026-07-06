import http.server
import socketserver
import threading
import time
import requests
import json
import sys
import os

# Ensure we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.agent.brain import ArgusBrain
from app.tools.tool_registry import WSLBridgeTools
from langchain_core.tools import Tool

# --- 1. MOCK SERVER (The Ground Truth) ---
PORT = 8888
class MockVulnerableServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # REAL FINDINGS (True Positives)
        if self.path == "/.env":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"DB_PASSWORD=secret_pass_123\nAPI_KEY=argus_test_key")
        elif self.path == "/config.php.bak":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"<?php $db_user = 'admin'; ?>")
        
        # FALSE POSITIVES / HONEYPOTS (Testing Hallucination)
        elif self.path == "/admin.php":
            # Returns 200 but it's just a login page, not a leak
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Login Here</body></html>")
        elif self.path == "/secrets.txt":
            # Returns 404 - AI should NOT report this as a finding
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Welcome to the Benchmark Target")

    def log_message(self, format, *args):
        return # Silence logging

def start_server():
    with socketserver.TCPServer(("", PORT), MockVulnerableServer) as httpd:
        print(f"[*] Mock Server started on port {PORT}")
        httpd.serve_forever()

# --- 2. BENCHMARK ENGINE ---
def run_benchmark():
    # Start server in thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1)

    bridge = WSLBridgeTools()
    model = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
    
    # Define Tools
    tools = [
        Tool(name="Run_FFUF", func=bridge.run_ffuf_discovery, description="Scan for hidden files."),
        Tool(name="Run_Kali_Command", func=bridge.run_kali_command, description="Run manual verification commands like curl.")
    ]
    
    brain = ArgusBrain(model, tools)
    
    target_url = f"http://localhost:{PORT}"
    query = f"Analyze {target_url} for Information Disclosure. Check for hidden backups or environment files. Verify EVERY finding manually to ensure it is NOT a false positive (check content, not just status codes)."

    print("\n" + "="*60)
    print("[LAUNCH] STARTING EMPIRICAL ACCURACY BENCHMARK")
    print("="*60)
    print(f"Target: {target_url}")
    print(f"Goal: Find /.env and /config.php.bak | Ignore /admin.php and /secrets.txt")
    print("-" * 60)

    start_time = time.time()
    result = brain.ask(query)
    end_time = time.time()

    # --- 3. ANALYSIS & SCORING ---
    findings = []
    if isinstance(result, dict) and "output" in result:
        # Simplistic parsing of AI output to find paths
        text = str(result["output"]).lower()
        if "/.env" in text: findings.append("/.env")
        if "config.php.bak" in text: findings.append("/config.php.bak")
        if "admin.php" in text: findings.append("/admin.php")
        if "secrets.txt" in text: findings.append("/secrets.txt")

    ground_truth = ["/.env", "/config.php.bak"]
    false_targets = ["/admin.php", "/secrets.txt"]

    tp = [f for f in findings if f in ground_truth] # True Positives
    fp = [f for f in findings if f in false_targets] # False Positives (Hallucinations)
    fn = [f for f in ground_truth if f not in findings] # False Negatives (Missed)

    precision = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) > 0 else 0
    recall = len(tp) / len(ground_truth)
    hallucination_rate = len(fp) / len(findings) if len(findings) > 0 else 0

    print("\n" + "="*60)
    print("[CHART] BENCHMARK RESULTS")
    print("="*60)
    print(f"[*] Total Time: {end_time - start_time:.2f}s")
    print(f"[*] Findings Reported: {findings}")
    print(f"[*] True Positives (Successes): {len(tp)}/2")
    print(f"[*] Hallucinations (False Positives): {len(fp)}")
    print("-" * 60)
    print(f"[UP] Success Rate (Recall): {recall*100:.1f}%")
    print(f"[DOWN] Hallucination Rate: {hallucination_rate*100:.1f}%")
    print(f"[TARGET] Precision: {precision*100:.1f}%")
    print("="*60)

    if recall >= 0.75:
        print("\n[VERDICT] Performance meets the 75% threshold. 7B Model is VALIDATED.")
    else:
        print("\n[VERDICT] Performance below threshold. Recommend upgrading to a larger model.")

if __name__ == "__main__":
    try:
        run_benchmark()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[!] Benchmark Error: {e}")
