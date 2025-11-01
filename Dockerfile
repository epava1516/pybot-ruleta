# syntax=docker/dockerfile:1

### 1) Etapa de build (opcional, solo para caché de dependencias)
FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
# Preinstalamos en builder para cachear capas, pero NO copiamos site-packages luego.
RUN pip install --upgrade pip && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

### 2) Etapa final (runtime) — aquí es donde debe quedar todo instalado
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Seguridad: usuario no root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --home-dir /app --no-create-home --shell /usr/sbin/nologin appuser

# Copiamos ruedas y requirements para instalar EN ESTA ETAPA
COPY --from=builder /wheels /wheels
COPY requirements.txt .

# Instalamos dependencias en la etapa final
RUN pip install --upgrade pip && pip install --no-cache-dir --find-links=/wheels -r requirements.txt

# Copiamos el código
COPY . .

# Permisos
RUN chown -R appuser:appgroup /app
USER appuser

# Puerto de la mini-app
EXPOSE 8080

# Healthcheck sin wget/curl (usa Python estándar)
HEALTHCHECK --interval=30s --timeout=3s --retries=5 CMD python - <<'PY'
import urllib.request, sys
try:
    with urllib.request.urlopen("http://127.0.0.1:8080/health", timeout=2) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY

ENTRYPOINT ["python", "main.py"]

