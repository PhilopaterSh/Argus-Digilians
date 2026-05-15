FROM python:3.11-slim

# ── System packages (all available in debian slim) ────────────────────────────
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    git \
    perl \
    nmap \
    nodejs \
    npm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Nikto (Perl script, cloned from GitHub) ───────────────────────────────────
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto \
    && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && chmod +x /opt/nikto/program/nikto.pl

# ── Gobuster (pre-built binary from GitHub releases) ──────────────────────────
RUN wget https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Linux_x86_64.tar.gz \
    && tar -xzf gobuster_Linux_x86_64.tar.gz \
    && mv gobuster /usr/local/bin/ \
    && rm gobuster_Linux_x86_64.tar.gz

# ── FFUF (pre-built binary from GitHub releases) ──────────────────────────────
RUN wget https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz \
    && tar -xzf ffuf_2.1.0_linux_amd64.tar.gz \
    && mv ffuf /usr/local/bin/ \
    && rm ffuf_2.1.0_linux_amd64.tar.gz

# ── Subfinder (pre-built binary from GitHub releases) ─────────────────────────
RUN wget https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip \
    && unzip subfinder_2.6.6_linux_amd64.zip \
    && mv subfinder /usr/local/bin/ \
    && rm subfinder_2.6.6_linux_amd64.zip

# ── Wappalyzer CLI (npm) ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y whatweb && apt-get clean && rm -rf /var/lib/apt/lists/*

# ── Wordlists ─────────────────────────────────────────────────────────────────
RUN mkdir -p /app/wordlists
ADD https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt \
    /app/wordlists/common.txt
RUN chmod 644 /app/wordlists/common.txt

# ── Python app ────────────────────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "main.py"]