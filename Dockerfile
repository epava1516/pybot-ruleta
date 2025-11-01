# syntax=docker/dockerfile:1

### 1) Etapa de build
FROM python:3.13-slim AS builder

# Variables de entorno para buena práctica
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Copia requisitos e instala dependencias
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copia el resto del código
COPY . .

# Dockerfile (corrige SOLO la parte final)
### 2) Etapa de producción
FROM python:3.13-slim AS runtime
WORKDIR /app

# Copia binarios/paquetes instalados en la etapa de build
COPY --from=builder /usr/local /usr/local
# Copia el código
COPY --from=builder /app /app

# Usuario no-root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --home-dir /app --no-create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appgroup /app
USER appuser

EXPOSE 8080
ENTRYPOINT ["python", "main.py"]

