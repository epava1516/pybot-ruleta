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

# --- Endpoint de webhook para Telegram (HTTPS llega por el proxy; aquí HTTP interno) ---
@web_bp.post("/telegram/<path:token>")
def telegram_webhook(token: str):
    webhook_path = current_app.config.get("WEBHOOK_PATH")
    ptb_app = current_app.config.get("PTB_APP")  # Application de PTB v20

    if not ptb_app or not webhook_path:
        return jsonify({"error": "webhook no inicializado"}), 500

    # Validar ruta
    if token != webhook_path:
        return jsonify({"error": "ruta inválida"}), 404

    try:
        update = Update.de_json(request.get_json(force=True), ptb_app.bot)
    except Exception as e:
        return jsonify({"error": f"payload inválido: {e}"}), 400

    # Procesar asíncronamente sin bloquear la respuesta
    asyncio.get_event_loop().create_task(ptb_app.process_update(update))
    return "", 200

