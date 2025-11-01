# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema si hicieran falta (comenta si no)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#  && rm -rf /var/lib/apt/lists/*

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

# Puerto HTTP de tu Flask
EXPOSE 8080

# HEALTHCHECK en forma CMD (sin heredoc)
# (El endpoint /health lo sirve Flask)
HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request,sys; \
u='http://127.0.0.1:8080/health'; \
r=urllib.request.urlopen(u, timeout=2); \
sys.exit(0 if r.status==200 else 1)" || exit 1

ENTRYPOINT ["python", "main.py"]

