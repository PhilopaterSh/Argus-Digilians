import sys, os
sys.path.insert(0, r'C:\AI_PenTest_Project\Argus')
from app.tools.wsl_bridge import WSLBridge, WSLConfig
from app.tools.command_runner import CommandRunner
cfg = WSLConfig()
bridge = WSLBridge(cfg)
cr = CommandRunner(bridge)
cmd = 'curl -I -sS --max-time 15 https://www.cultbeauty.co.uk'
try:
    out = cr._run_direct_wsl(cmd, show_prompt=True)
    print('OUT START')
    print(repr(out)[:2000])
    print('OUT END')
except Exception as e:
    import traceback
    print('EXC TYPE:', type(e))
    print('EXC:', repr(e))
    traceback.print_exc()
