from flask import render_template, request, current_app, jsonify
from . import web_bp
from telegram import Update
import asyncio

@web_bp.get("/")
def index():
    chat_id = request.args.get("chat_id", default="")
    return render_template("index.html", chat_id=chat_id)

@web_bp.get("/health")
def health():
    return {"status": "ok"}

# --- Webhook Telegram: ruta fija y verificación por cabecera secreta ---
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

