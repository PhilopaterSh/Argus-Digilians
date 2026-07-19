# Argus agent image for the containerized lab (specs/014-containerized-lab).
# Reconstructed + modernized from origin/argus/SALMA:Agent_Containers/Dockerfile:
#   - base bumped to Python 3.12 (canonical, 012 section 2.6)
#   - same pinned recon toolset (nmap, nikto, gobuster 3.6.0, ffuf 2.1.0, subfinder 2.6.6, whatweb)
#   - runs the CURRENT app/ codebase (not the historical main.py)
#
# Build context is the repository root (see docker-compose.yml build.context).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# System packages + recon tools available via apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    curl \
    git \
    perl \
    nmap \
    whatweb \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Nikto (Perl script, cloned from GitHub)
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto \
    && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && chmod +x /opt/nikto/program/nikto.pl

# Gobuster (pinned release binary)
RUN wget -q https://github.com/OJ/gobuster/releases/download/v3.6.0/gobuster_Linux_x86_64.tar.gz \
    && tar -xzf gobuster_Linux_x86_64.tar.gz \
    && mv gobuster /usr/local/bin/ \
    && rm gobuster_Linux_x86_64.tar.gz

# FFUF (pinned release binary)
RUN wget -q https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz \
    && tar -xzf ffuf_2.1.0_linux_amd64.tar.gz \
    && mv ffuf /usr/local/bin/ \
    && rm ffuf_2.1.0_linux_amd64.tar.gz

# Subfinder (pinned release binary)
RUN wget -q https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip \
    && unzip -q subfinder_2.6.6_linux_amd64.zip \
    && mv subfinder /usr/local/bin/ \
    && rm subfinder_2.6.6_linux_amd64.zip

WORKDIR /argus

# Python dependencies (runtime requirements of the current app/)
COPY config/requirements.txt /argus/requirements.txt
RUN pip install --no-cache-dir -r /argus/requirements.txt

# Current application code (redesign onto app/, not the legacy main.py)
COPY app/ /argus/app/
COPY scripts/ /argus/scripts/
COPY config.yaml /argus/config.yaml

ENV PYTHONPATH=/argus

# Default: the compose file keeps the container alive so recon runs are launched via
# `docker exec my-agent python scripts/run_agent.py --target $TARGET_URL`.
CMD ["python", "-c", "print('Argus agent image ready. Run: docker exec my-agent python scripts/run_agent.py --target $TARGET_URL')"]
