# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instala requirements primero (mejor caché)
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia el código
COPY . .

# Crea usuario no-root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --home-dir /app --no-create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appgroup /app
USER appuser

# Puerto usado por el servidor webhook (solo si MODE=webhook)
EXPOSE 8080

# HEALTHCHECK salta en modo polling (sin servidor HTTP)
HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD python -c "import os, sys, urllib.request; mode=os.getenv('MODE','polling').lower(); port=os.getenv('WEB_PORT','8080'); if mode != 'webhook': sys.exit(0); url=f'http://127.0.0.1:{port}/health'; resp=urllib.request.urlopen(url, timeout=2); sys.exit(0 if resp.status==200 else 1)" || exit 1

ENTRYPOINT ["python", "main.py"]
