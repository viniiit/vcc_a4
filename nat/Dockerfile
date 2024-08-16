FROM ubuntu:latest

# Install Python and pip
RUN apt update && \
    apt install -y python3 python3-pip iptables

# Force pip to install packages globally
RUN pip install --break-system-packages requests
