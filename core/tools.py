import subprocess

class WSLTools:
    def __init__(self, distro="kali-linux"):
        self.distro = distro

    def run(self, command):
        try:
            full_cmd = f"wsl -d {self.distro} bash -c \"{command}\""
            res = subprocess.run(full_cmd, capture_output=True, text=True, shell=True)
            return res.stdout if res.returncode == 0 else f"Error: {res.stderr}"
        except Exception as e:
            return f"Exception: {str(e)}"

    def recon_suite(self, url):
        """Runs the standard recon suite."""
        ww = self.run(f"whatweb {url}")
        cl = self.run(f"curl -skI -A 'Mozilla/5.0' {url}")
        wg = self.run(f"wget -q -O - --no-check-certificate --user-agent='Mozilla/5.0' {url} | head -n 30")
        return {
            "whatweb": ww,
            "curl": cl,
            "wget": wg
        }
