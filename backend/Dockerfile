# /home/nils/fallen_bugie/backend/Dockerfile
FROM python:3.11-slim

# Installiere Nmap, Wget und Unzip (für Nuclei)
RUN apt-get update && apt-get install -y nmap wget unzip curl

# Installiere Nuclei (zieht sich die neueste Version)
RUN wget https://github.com/projectdiscovery/nuclei/releases/download/v3.3.0/nuclei_3.3.0_linux_amd64.zip && \
    unzip nuclei_3.3.0_linux_amd64.zip && \
    mv nuclei /usr/local/bin/ && \
    rm nuclei_3.3.0_linux_amd64.zip

# Arbeitsverzeichnis im Container
WORKDIR /app

# Kopiere zuerst die Requirements und installiere sie (spart Zeit beim Neuladen)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Backend-Code
COPY . .

# Setze den Python-Pfad, damit Celery die App findet
ENV PYTHONPATH=/app