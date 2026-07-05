"""Read the Streamlit port from config.yaml and print it to stdout."""
import os
import yaml

config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
with open(config_path, encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

print(cfg["streamlit"]["port"])
