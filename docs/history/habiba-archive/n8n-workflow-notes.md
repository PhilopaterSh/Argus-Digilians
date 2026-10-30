# n8n on WSL Kali: Host Access Setup Guide

This document describes how to set up n8n using Docker Compose within a WSL Kali environment, enabling n8n to access tools installed directly on the Kali host (such as nmap) via the SSH protocol.

## 1. Rationale (The Logic)
When n8n runs inside a Docker container, it is isolated from the host Kali system. To access Kali tools without reinstalling them inside the container, we use SSH as a bridge. n8n sends commands to the host Kali system and receives the output as if it were running locally.

---

## 2. Practical Steps

### Step 1: Prepare SSH on Kali (Host)
The Kali system must be able to receive SSH connections from the container.

1. Install SSH Server:
   ```bash
   sudo apt update && sudo apt install openssh-server -y
   ```
2. Modify configuration to allow access:
   Edit /etc/ssh/sshd_config to ensure password or key-based authentication is enabled.
3. Start the service:
   ```bash
   sudo service ssh start
   ```

### Step 2: Docker Compose Setup
Create a docker-compose.yml file to run n8n.

```yaml
version: '3.8'

services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    container_name: n8n_wsl
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - NODE_FUNCTION_ALLOW_EXTERNAL=ssh2
    volumes:
      - ./n8n_data:/home/node/.n8n
      - ./scripts:/home/node/scripts
```

### Step 3: Accessing Tools from n8n
Inside the n8n interface, you have two options to run Kali tools:

#### (A) Using the "SSH Node" (Recommended):
1. Add an SSH node.
2. In the Credentials settings, use:
   - Host: host.docker.internal (This address always points to the Kali host from inside Docker).
   - Port: 22
   - User: Your Kali username.
3. In the Command field, enter your command: nmap -sV 192.168.1.1

#### (B) Using the "Execute Command Node":
If you install an SSH client inside the container, you can run:
```bash
ssh user@host.docker.internal "nmap -sP 10.0.0.0/24"
```

---

## 3. Handling Python Scripts and Libraries
Since we mapped the ./scripts volume:
1. Place your .py files in the scripts folder on your host.
2. Inside n8n, they are accessible at /home/node/scripts.
3. To run them, it is recommended to use the SSH node to execute them using the host's Python environment (which contains all your pre-installed libraries).

---

## 4. Portability
To move this setup to another machine:
1. Copy the entire directory (docker-compose.yml, n8n_data, scripts).
2. Ensure SSH is enabled on the new Kali host.
3. Run: docker-compose up -d
4. All workflows will work immediately because they reference the constant host.docker.internal address.

---

Security Note: Ensure you change your Kali password and secure the SSH service, as you are opening a port for internal communication.
