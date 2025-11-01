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

### 2) Etapa de producción
FROM python:3.13-slim AS runtime

WORKDIR /app

# Crea usuario no-root para mayor seguridad
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --home-dir /app --no-create-home --shell /usr/sbin/nologin appuser

# Copia desde builder
COPY --from=builder /app /app

# Ajusta permisos
RUN chown -R appuser:appgroup /app

USER appuser

# Expone puerto si tu web lo requiere (ajústalo)
EXPOSE 8080

# Define el comando de inicio (ajústalo según tu main.py/app)
ENTRYPOINT ["python", "main.py"]

