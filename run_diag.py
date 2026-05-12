import subprocess
import time
import os

# Kill any existing streamlit processes
subprocess.run("taskkill /IM streamlit.exe /F", shell=True, capture_output=True)

# Run streamlit in background
cmd = [r".venv\Scripts\python.exe", "-m", "streamlit", "run", "test_paramiko_streamlit.py", "--server.headless", "true"]
with open("streamlit_output.log", "w") as f:
    proc = subprocess.Popen(cmd, stdout=f, stderr=f)

print(f"Started streamlit with PID {proc.pid}")
time.sleep(10) # Wait for it to initialize and run the script

# Since streamlit is a server, it might not "finish" running the script in a way that shows in stdout easily 
# if it's just the server logs. 
# But our script test_paramiko_streamlit.py runs on load.

# Let's try to use a simple python script first to see if it works there.
with open("python_import_test.log", "w") as f:
    subprocess.run([r".venv\Scripts\python.exe", "-c", "import sys; import paramiko; print(f'Python: {sys.executable}'); print(f'Paramiko: {paramiko.__file__}')"], stdout=f, stderr=f)

proc.terminate()
