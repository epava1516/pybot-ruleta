# 0) Toma DOMAIN y EMAIL del .env (solo estas dos)
export DOMAIN="$(grep '^DOMAIN=' .env | cut -d= -f2)"
export EMAIL="$(grep  '^EMAIL='  .env | cut -d= -f2)"

# 1) Libera el 80 (para standalone)
docker compose down

# 2) Asegura el directorio de LE en el host
sudo mkdir -p ./certbot/conf

# 3) Emite el certificado con nombre EXACTO = $DOMAIN
docker run --rm -p 80:80 \
  -v "$PWD/certbot/conf:/etc/letsencrypt" \
  certbot/certbot:latest certonly --standalone \
  --preferred-challenges http \
  --cert-name "$DOMAIN" -d "$DOMAIN" -m "$EMAIL" \
  --agree-tos --non-interactive

# 4) Comprueba que ahora existe la ruta SIN sufijo
sudo ls -l "./certbot/conf/live/$DOMAIN/fullchain.pem" "./certbot/conf/live/$DOMAIN/privkey.pem"

# 5) Sube el stack normal y recarga Nginx
docker compose up -d
docker compose kill -s HUP nginx-proxy || docker compose exec nginx-proxy nginx -s reload || true

# 6) Prueba
curl -I "https://${DOMAIN}/health"
