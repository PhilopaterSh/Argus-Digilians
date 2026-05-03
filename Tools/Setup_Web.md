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

## Execution Summary
To perform a quick manual analysis of a target, run these commands in sequence:

1. whatweb --no-errors -v http://target.com
2. curl -v -k http://target.com
3. wget --spider --server-response http://target.com
