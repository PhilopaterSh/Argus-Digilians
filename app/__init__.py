# Argus Security Framework - App Package
import logging
import os

# Load configuration from config.yaml (fallback to INFO)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
if os.path.exists(CONFIG_PATH):
    try:
        import yaml
        with open(CONFIG_PATH) as cfg:
            cfg_data = yaml.safe_load(cfg)
        level_name = cfg_data.get('log_level', 'INFO')
    except Exception:
        level_name = 'INFO'
else:
    level_name = 'INFO'

logging.basicConfig(level=getattr(logging, level_name.upper(), logging.INFO),
                    format='[%(asctime)s] %(levelname)s: %(message)s')
