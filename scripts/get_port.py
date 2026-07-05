"""Read the Streamlit port from config.yaml and print it to stdout."""
import os
import sys
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')

if not os.path.exists(CONFIG_PATH):
    print("8501", file=sys.stderr)
    sys.exit(1)

try:
    with open(CONFIG_PATH, 'r') as f:
        cfg = yaml.safe_load(f) or {}
    port = cfg.get("streamlit", {}).get("port", 8501)
    print(port)
except Exception:
    print("8501", file=sys.stderr)
    sys.exit(1)
