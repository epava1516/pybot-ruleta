import os
import sys
import secrets
from urllib.parse import urlparse


def _normalize_domain(domain: str) -> str:
    domain = domain.strip()
    if not domain:
        return ""

    # Acepta dominios con o sin esquema y descarta cualquier ruta o query
    parsed = urlparse(domain if "://" in domain else f"//{domain}", scheme="https")
    return (parsed.hostname or "").strip()


def _normalize_public_url(public_url: str | None, domain: str) -> str:
    if public_url and public_url.strip():
        url = public_url.strip()
    else:
        url = f"https://{domain}"

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    return url.rstrip("/")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# -----------------------------
# Variables de entorno obligatorias
# -----------------------------
TOKEN = os.getenv("TOKEN")
DOMAIN_RAW = os.getenv("DOMAIN")

if not TOKEN or not DOMAIN_RAW:
    print("ERROR: Las variables de entorno TOKEN y DOMAIN deben estar definidas.")
    sys.exit(1)

DOMAIN = _normalize_domain(DOMAIN_RAW)

if not DOMAIN:
    print("ERROR: La variable de entorno DOMAIN no contiene un dominio válido.")
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
# Modo de ejecución del bot y URLs auxiliares
# -----------------------------
MODE = os.getenv("MODE", "polling").lower()  # "polling" | "webhook"
PUBLIC_URL = _normalize_public_url(os.getenv("PUBLIC_URL"), DOMAIN)
REDIRECT_URL = os.getenv("REDIRECT_URL", "https://thehomelesssherlock.com/")

RESTRICT_TO_TELEGRAM = _as_bool(os.getenv("RESTRICT_TO_TELEGRAM"), False)
GATE_STRICT = _as_bool(os.getenv("GATE_STRICT"), False)

# Secreto para cabecera X-Telegram-Bot-Api-Secret-Token
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or secrets.token_urlsafe(24)
WEBHOOK_URL = f"{PUBLIC_URL}/telegram/webhook"

# -----------------------------
# Imprimir configuración para debug (omite en producción)
# -----------------------------
if ENVIRONMENT.lower() != "production":
    print(f"CONFIG --> TOKEN=[***hidden***], DOMAIN_RAW={DOMAIN_RAW}, DOMAIN={DOMAIN}")
    print(f"CONFIG --> DATA_FILE={DATA_FILE}")
    print(f"CONFIG --> DEFAULT_WINDOW={DEFAULT_WINDOW}, DEFAULT_DATA_LIMIT={DEFAULT_DATA_LIMIT}")
    print(f"CONFIG --> MODE={MODE}, PUBLIC_URL={PUBLIC_URL}")
    print(f"CONFIG --> WEBHOOK_URL={WEBHOOK_URL}")
    print(f"CONFIG --> ENVIRONMENT={ENVIRONMENT}, LOG_LEVEL={LOG_LEVEL}")
    print(f"CONFIG --> RESTRICT_TO_TELEGRAM={RESTRICT_TO_TELEGRAM}, GATE_STRICT={GATE_STRICT}")
