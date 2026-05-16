# Web Analysis Tools Setup and Usage Guide

This document provides a guide for the essential web analysis tools used in this project, including verification, installation, and usage patterns.

---

## 1. WhatWeb

### Technical Description
WhatWeb identifies website technologies. It can recognize Content Management Systems (CMS), blogging platforms, statistic/analytics packages, JavaScript libraries, and web server versions.

### Installation and Verification
To check if the tool is installed or to install it on a Debian-based system:

```bash
# Check installation
whatweb --version

# Install if missing
sudo apt update && sudo apt install -y whatweb
```

### Usage Examples
The following command is used for detailed technology analysis without color formatting:

```bash
whatweb --no-errors -v --color=never https://example.com
```

- --no-errors: Ignores connection errors.
- -v: Enables verbose output.
- --color=never: Disables color formatting for cleaner text logs.

---

## 2. Curl

### Technical Description
Curl is a command-line tool for transferring data with URLs. In security testing, it is primarily used to inspect HTTP headers, cookies, and server configurations.

### Installation and Verification
To check if the tool is installed or to install it:

```bash
# Check installation
curl --version

# Install if missing
sudo apt update && sudo apt install -y curl
```

### Usage Examples
The following command retrieves full headers and connection details:

```bash
curl -v -k https://example.com
```

- -v: Shows complete request and response headers (Verbose).
- -k: Ignores SSL certificate warnings.

---

## 3. Wget

### Technical Description
Wget is a utility for retrieving content from web servers. It is used in this project to analyze server responses and track redirections without downloading the actual files.

### Installation and Verification
To check if the tool is installed or to install it:

```bash
# Check installation
wget --version

# Install if missing
sudo apt update && sudo apt install -y wget
```

### Usage Examples
The following command simulates a spider crawl to check server responses:

```bash
wget --spider --server-response --max-redirect=5 https://example.com
```

- --spider: Does not download any files; only checks if the URL is available.
- --server-response: Prints the full server response headers.
- --max-redirect=5: Limits the number of redirections to follow.

---

## 4. Nmap (Network Mapper)

### Technical Description
Nmap is used for network discovery and security auditing. In Argus, it is employed for service version detection and identifying open ports.

### Usage in Argus
```bash
nmap -F --open -sV <target>
```
- `-F`: Fast mode (scans top 100 ports).
- `--open`: Shows only open ports.
- `-sV`: Probes open ports to determine service/version info.

---

## 5. Wafw00f (WAF Detection)

### Technical Description
Identifies and fingerprints Web Application Firewalls (WAF) protecting a website. Essential for determining if active exploitation or aggressive scanning is feasible.

### Usage in Argus
```bash
wafw00f <url>
```

---

## 6. Subdomain Discovery (Passive & Active)

Argus utilizes a multi-layered approach to map the attack surface:
- **Passive:** `subfinder`, `assetfinder`, `findomain`, `chaos-client`.
- **Active (Brute-Force):** `gobuster`, `ffuf`, `fierce`, `amass`.
- **Discovery Tooling:** `theHarvester` for OSINT-based discovery.

---

## 7. DNS Resolution & Permutation

To ensure maximum accuracy and expansion:
- **MassDNS:** High-performance DNS stub resolver for mass resolution.
- **PureDNS:** A powerful resolver that filters out wildcards and dead domains.
- **DNSGen & AltDNS:** Generate permutations and alterations of discovered subdomains to find hidden assets.

---

## 8. Advanced Reconnaissance Frameworks

Argus integrates several high-impact frameworks for automated intelligence:
- **Osmedeus:** A powerful offensive security framework for automated reconnaissance.
- **SpiderFoot:** The ultimate OSINT automation tool with 100+ data sources.
- **FinalRecon:** Fast multi-purpose recon (Headers, Whois, SSL).
- **Ph.Sh Suite:** Advanced URL extraction and subdomain analysis.

---

## Execution Summary (Argus 5-Phase Workflow)
The Argus AI Agent follows this professional pentesting sequence:

1.  **Phase 1: Passive Recon (OSINT):** Gathering data from third-party sources (Amass, Subfinder).
2.  **Phase 2: Active Recon (Brute-Force):** Direct probing and wordlist-based guessing (FFuf, Gobuster).
3.  **Phase 3: Permutation & Expansion:** Generating and testing subdomain variations (DNSGen, AltDNS).
4.  **Phase 4: DNS Resolution & Validation:** Filtering results and verifying active hosts (MassDNS, PureDNS).
5.  **Phase 5: Deep Analysis & Verification:** Service fingerprinting and final intelligence gathering (Nmap, WhatWeb, Osmedeus).
