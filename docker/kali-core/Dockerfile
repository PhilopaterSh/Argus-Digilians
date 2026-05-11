FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        iputils-ping \
        openssh-server \
        whatweb \
        wget \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash kali \
    && echo "kali:kali" | chpasswd \
    && mkdir -p /var/run/sshd \
    && sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
    && sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config

# Install ProjectDiscovery httpx when the Kali package is unavailable or not the desired tool.
RUN curl -L https://github.com/projectdiscovery/httpx/releases/download/v1.7.1/httpx_1.7.1_linux_amd64.zip -o /tmp/httpx.zip \
    && apt-get update \
    && apt-get install -y --no-install-recommends unzip \
    && unzip /tmp/httpx.zip -d /tmp/httpx \
    && install /tmp/httpx/httpx /usr/local/bin/httpx \
    && rm -rf /tmp/httpx /tmp/httpx.zip /var/lib/apt/lists/*

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]
