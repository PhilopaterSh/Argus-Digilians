FROM python:3.11-slim

# Install system dependencies, Go, and clean up
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    ffuf \
    && wget https://github.com/projectdiscovery/subfinder/releases/download/v2.6.6/subfinder_2.6.6_linux_amd64.zip \
    && unzip subfinder_2.6.6_linux_amd64.zip \
    && mv subfinder /usr/local/bin/ \
    && rm subfinder_2.6.6_linux_amd64.zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Create a directory for wordlists and a basic list for the lab
RUN mkdir -p /app/wordlists
ADD https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt /app/wordlists/common.txt

RUN chmod 644 /app/wordlists/common.txt

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "main.py"]