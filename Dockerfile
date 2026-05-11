# ARGUS STUDIO - DOCKER ORCHESTRATED EDITION
FROM python:3.11-slim

WORKDIR /app

# Install Python requirements
COPY Library_Python_Requirements/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment Defaults for Docker Kali-Core Bridge
ENV WSL_HOST=kali-core
ENV WSL_USER=kali
ENV WSL_PASS=kali
ENV WSL_PORT=22

EXPOSE 12189

CMD ["streamlit", "run", "GUI/app.py", "--server.port", "12189", "--server.address", "0.0.0.0"]
