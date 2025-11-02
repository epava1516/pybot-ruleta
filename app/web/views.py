from flask import render_template, request, current_app, jsonify, redirect, make_response
from . import web_bp
from telegram import Update
import asyncio

# Verificador de WebApp
from app.utils.tg_webapp import verify_init_data

# -------------------- Guard opcional (antes de cada request) --------------------
@web_bp.before_app_request
def gate_non_telegram():
    """
    Si RESTRICT_TO_TELEGRAM=True:
      - Excepciones: /health, /telegram/webhook, /api/*, /statics/*
      - Si GATE_STRICT=False: NO bloquea /; deja cargar y que el front verifique.
      - Si GATE_STRICT=True: bloquea / si no hay cookie tg_ok=1 -> REDIRECT_URL
    """
    cfg = current_app.config
    if not cfg.get("RESTRICT_TO_TELEGRAM", False):
        return  # sin restricciones

    path = request.path or "/"
    if path == "/health" or path == "/telegram/webhook":
        return
    if path.startswith("/api/") or path.startswith("/statics/"):
        return

    # ¿ya verificado por cookie?
    if request.cookies.get("tg_ok") == "1":
        return

    # Si el modo estricto está activado, redirige fuera de inmediato.
    if cfg.get("GATE_STRICT", False):
        return redirect(cfg.get("REDIRECT_URL"), code=302)
    # Si no es estricto, dejamos pasar para que el front haga la verificación
    # con /api/session/verify y ponga la cookie tg_ok. (Ver snippet JS más abajo)


# -------------------- Rutas web --------------------
@web_bp.get("/")
def index():
    chat_id = request.args.get("chat_id", default="")
    return render_template("index.html", chat_id=chat_id)

@web_bp.get("/health")
def health():
    return {"status": "ok"}

# -------------------- Sesión WebApp (verificación HMAC) --------------------
@web_bp.post("/api/session/verify")
def api_session_verify():
    """
    Front debe enviar { initData: Telegram.WebApp.initData }.
    Si es válido, devolvemos cookie tg_ok=1.
    """
    data = request.get_json(silent=True) or {}
    init_data = data.get("initData", "")
    token = current_app.config.get("TOKEN", "")

    if verify_init_data(init_data, token):
        resp = jsonify(ok=True)
        # Cookie de sesión: segura y apta para WebView
        resp.set_cookie(
            "tg_ok",
            "1",
            max_age=3600,
            secure=True,
            httponly=False,   # debe ser accesible por el WebView si hicieras comprobaciones en front
            samesite="None",  # para webview embebido
        )
        return resp
    return jsonify(ok=False), 403


# -------------------- Webhook Telegram --------------------
@web_bp.post("/telegram/webhook")
def telegram_webhook():
    ptb_app = current_app.config.get("PTB_APP")
    ptb_loop = current_app.config.get("PTB_LOOP")
    secret_expected = current_app.config.get("WEBHOOK_SECRET")

    if not ptb_app or not ptb_loop:
        return jsonify({"error": "webhook no inicializado"}), 500

    # Verifica el secret header oficial de Telegram si lo hemos configurado
    recv_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret_expected and recv_secret != secret_expected:
        return jsonify({"error": "forbidden"}), 403

    try:
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    except Exception as e:
        return jsonify({"error": f"payload inválido: {e}"}), 400

    # Encola el procesamiento en el loop donde corre PTB
    asyncio.run_coroutine_threadsafe(ptb_app.process_update(update), ptb_loop)
    return "", 200

