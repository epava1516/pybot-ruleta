# Bot de Telegram

El repositorio ahora contiene únicamente el backend del bot de Telegram. Todo el
código vive en `./backend` y el `docker-compose.yml` construye la imagen a partir
de ese directorio.

## Despliegue con TLS propio

1. Exporta el dominio y correo definidos en `.env`:

   ```bash
   export DOMAIN="$(grep '^DOMAIN=' .env | cut -d= -f2)"
   export EMAIL="$(grep  '^EMAIL='  .env | cut -d= -f2)"
   ```

2. Libera el puerto 80 si estás reutilizando contenedores previos:

   ```bash
   docker compose down
   ```

3. Asegura el directorio de certificados en el host:

   ```bash
   sudo mkdir -p ./certbot/conf
   ```

4. Emite el certificado con **nombre exacto** `$DOMAIN`:

   ```bash
   docker run --rm -p 80:80 \
     -v "$PWD/certbot/conf:/etc/letsencrypt" \
     certbot/certbot:latest certonly --standalone \
     --preferred-challenges http \
     --cert-name "$DOMAIN" -d "$DOMAIN" -m "$EMAIL" \
     --agree-tos --non-interactive
   ```

5. Comprueba que existen los certificados esperados (sin sufijos):

   ```bash
   sudo ls -l "./certbot/conf/live/$DOMAIN/fullchain.pem" "./certbot/conf/live/$DOMAIN/privkey.pem"
   ```

6. Levanta el stack habitual y recarga Nginx:

   ```bash
   docker compose up -d
   docker compose kill -s HUP nginx-proxy || docker compose exec nginx-proxy nginx -s reload || true
   ```

7. Verifica el health-check expuesto por Nginx:

   ```bash
   curl -I "https://${DOMAIN}/health"
   ```
