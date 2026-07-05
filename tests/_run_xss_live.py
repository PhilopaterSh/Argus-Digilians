import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.tools import WSLBridgeTools

target = sys.argv[1] if len(sys.argv) > 1 else "http://testasp.vulnweb.com"
print(bridge := WSLBridgeTools())
print(bridge.check_xss(target))