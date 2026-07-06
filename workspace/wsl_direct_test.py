import subprocess
wsl_cmd = ['wsl','-d','kali-linux','-u','kali','bash','-c','curl -I -sS --max-time 15 https://www.cultbeauty.co.uk']
print('CMD:', wsl_cmd)
res = subprocess.run(wsl_cmd, capture_output=True, text=False, timeout=60)
print('Returncode:', res.returncode)
print('Stdout type:', type(res.stdout))
print('Stdout repr start:', repr(res.stdout)[:500])
print('Stderr type:', type(res.stderr))
print('Stderr repr start:', repr(res.stderr)[:500])
