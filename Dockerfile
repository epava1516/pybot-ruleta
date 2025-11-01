# Dockerfile
# syntax=docker/dockerfile:1

### 1) Etapa de build
FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

### 2) Etapa de producción
FROM python:3.13-slim AS runtime

WORKDIR /app

# Usuario no-root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --home-dir /app --no-create-home --shell /usr/sbin/nologin appuser

# Copia artefactos
COPY --from=builder /app /app

# Permisos
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8080

# HEALTHCHECK en exec form (sin curl/wget)
HEALTHCHECK --interval=30s --timeout=3s --retries=5 CMD \
  ["python","-c","import urllib.request,sys; \
u=urllib.request.urlopen('http://127.0.0.1:8080/health',timeout=2); \
sys.exit(0 if u.status==200 else 1)"]

ENTRYPOINT ["python", "main.py"]

