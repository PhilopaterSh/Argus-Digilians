import sys
sys.path.insert(0, r'C:\AI_PenTest_Project\Argus')
from app.tools.wsl_bridge import WSLConfig
c = WSLConfig()
print('HOST:', c.host)
print('USER:', repr(c.user))
print('DISTRO:', repr(c.distro))
print('PORT:', c.port)
print('PASSWORD repr:', repr(c.password))
