import os
import sys

# -----------------------------
# Variables de entorno obligatorias
# -----------------------------
TOKEN = os.getenv("TOKEN")
DOMAIN = os.getenv("DOMAIN")

if not TOKEN or not DOMAIN:
    print("ERROR: Las variables de entorno TOKEN y DOMAIN deben estar definidas.")
    sys.exit(1)

# -----------------------------
# Variables de entorno opcionales / con valor por defecto
# -----------------------------
DATA_FILE = os.getenv("DATA_FILE", "data/rolls.json")

DEFAULT_WINDOW = int(os.getenv("DEFAULT_WINDOW", 15))
DEFAULT_DATA_LIMIT = os.getenv("DEFAULT_DATA_LIMIT")
if DEFAULT_DATA_LIMIT is not None and DEFAULT_DATA_LIMIT.strip() != "":
    try:
        DEFAULT_DATA_LIMIT = int(DEFAULT_DATA_LIMIT)
    except ValueError:
        print("WARNING: DEFAULT_DATA_LIMIT no es numérico; usando None")
        DEFAULT_DATA_LIMIT = None
else:
    DEFAULT_DATA_LIMIT = None

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# -----------------------------
# Webhook URL para Telegram
# -----------------------------
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", TOKEN)  # puedes definir ruta personalizada si quieres
WEBHOOK_URL = f"https://{DOMAIN}/{WEBHOOK_PATH}"

# -----------------------------
# Imprimir configuración para debug (omite en producción)
# -----------------------------
if ENVIRONMENT.lower() != "production":
    print(f"CONFIG --> TOKEN=[***hidden***], DOMAIN={DOMAIN}")
    print(f"CONFIG --> DATA_FILE={DATA_FILE}")
    print(f"CONFIG --> DEFAULT_WINDOW={DEFAULT_WINDOW}, DEFAULT_DATA_LIMIT={DEFAULT_DATA_LIMIT}")
    print(f"CONFIG --> WEBHOOK_URL={WEBHOOK_URL}")
    print(f"CONFIG --> ENVIRONMENT={ENVIRONMENT}, LOG_LEVEL={LOG_LEVEL}")

