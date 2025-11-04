# Bot de Telegram

El repositorio contiene únicamente el backend del bot de Telegram. Todo el código
vive en `./backend` y la imagen Docker se construye a partir de ese directorio.

## Variables de entorno

El archivo `.env` es la fuente de verdad. Los valores actuales que utiliza el
bot son:

- `TOKEN` y `DOMAIN` **(obligatorias)**.
- `PUBLIC_URL`, `WEBHOOK_SECRET`, `MODE`, `WEB_HOST`, `WEB_PORT` para el modo
  webhook (el bot expone `/telegram/webhook` internamente y espera recibir las
  peticiones desde el dominio público definido).
- `DATA_FILE`, `DEFAULT_WINDOW`, `DEFAULT_DATA_LIMIT` para la persistencia de
  tiradas.
- `ENVIRONMENT`, `LOG_LEVEL`, `RESTRICT_TO_TELEGRAM`, `GATE_STRICT`,
  `REDIRECT_URL` para ajustar comportamiento auxiliar.

Si un valor no está definido en `.env` se usará el que aparece como defecto en
`backend/config.py`.

## Puesta en marcha con Docker

1. Crea los directorios de datos si aún no existen:

   ```bash
   mkdir -p data
   ```

2. Arranca el bot:

   ```bash
   docker compose up -d
   ```

   El servicio se llama `bot` y monta `./data` dentro del contenedor para
   persistir `data/rolls.json`.

3. El modo por defecto es *polling*. Si necesitas usar webhooks, asegura que:

   - `MODE=webhook` y `PUBLIC_URL` apuntan al dominio con certificado TLS.
   - El puerto `WEB_PORT` está expuesto (por defecto `8080`). El `docker-compose`
     ya publica `WEB_PORT` hacia el host. Termina TLS con el proxy que prefieras
     (Traefik, Caddy, Nginx externo, etc.) apuntando al contenedor.

4. Para ver los logs:

   ```bash
   docker compose logs -f bot
   ```

Para detener el servicio usa `docker compose down`.
