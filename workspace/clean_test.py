import sys
sys.path.insert(0, r'C:\AI_PenTest_Project\Argus')
from app.tools.wsl_bridge import WSLBridge, WSLConfig
from app.tools.command_runner import CommandRunner
from app.tools.utils import clean_ansi_codes
import subprocess

wsl_cmd = ['wsl','-d','kali-linux','-u','kali','bash','-c','curl -I -sS --max-time 15 https://www.cultbeauty.co.uk']
res = subprocess.run(wsl_cmd, capture_output=True, text=False, timeout=60)
raw = res.stdout if res.stdout else res.stderr
print('raw type:', type(raw))
try:
    if isinstance(raw, bytes):
        output = raw.decode('utf-8','replace')
    else:
        output = str(raw)
    print('decoded length', len(output))
    # call clean_ansi_codes
    cleaned = clean_ansi_codes(output)
    print('cleaned length', len(cleaned))
except Exception as e:
    import traceback
    print('EXC:', type(e), repr(e))
    traceback.print_exc()

# test waf detection
cr = CommandRunner(WSLBridge(WSLConfig()))
try:
    print('is_waf_blocked?', cr._is_waf_blocked(cleaned))
except Exception as e:
    print('EXC in waf check:', type(e), e)
