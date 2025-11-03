from flask import render_template, request, current_app, jsonify, redirect, make_response, Response
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
      - Excepciones: /health, /telegram/webhook, /api/*, /static/*, /gate
      - Si GATE_STRICT=False: NO bloquea /; deja cargar y que el front verifique.
      - Si GATE_STRICT=True: bloquea / si no hay cookie tg_ok=1 -> REDIRECT_URL
    """
    cfg = current_app.config
    if not cfg.get("RESTRICT_TO_TELEGRAM", False):
        return  # sin restricciones

    path = (request.path or "/").rstrip("/") or "/"

    # Rutas siempre permitidas
    if path in ("/health", "/gate", "/telegram/webhook"):
        return
    if path.startswith("/api/") or path.startswith("/static/"):
        return

    # ¿ya verificado por cookie?
    if request.cookies.get("tg_ok") == "1":
        return

    # Modo estricto: redirige de inmediato fuera de Telegram
    if cfg.get("GATE_STRICT", False):
        return redirect(cfg.get("REDIRECT_URL"), code=302)
    # Modo laxo: deja pasar y que el front haga /api/session/verify
    return


# -------------------- Rutas web --------------------
@web_bp.get("/")
def index():
    # Compat: ya no dependemos de ?chat_id, pero lo dejamos por si pruebas antiguas
    chat_id = request.args.get("chat_id", default="")
    return render_template("index.html", chat_id=chat_id)

@web_bp.get("/health")
def health():
    return {"status": "ok"}

@web_bp.get("/gate")
def gate():
    """
    Página mínima de acceso:
     - Si NO hay Telegram.WebApp -> redirige a REDIRECT_URL.
     - Si hay Telegram.WebApp -> POST /api/session/verify con initData y luego redirige a ?next=...
    """
    redir = current_app.config.get("REDIRECT_URL", "https://example.com/")
    next_url = request.args.get("next") or "/"

    # HTML mínimo inline para no depender de templates
    html = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Entrando…</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
</head>
<body>
  <script>
    (async function(){{
      const tg = window.Telegram && window.Telegram.WebApp;
      const next = {next_url!r};
      const fallback = {redir!r};

      try {{ tg && tg.ready && tg.ready(); }} catch(e) {{}}

      // Si no estamos dentro del WebView de Telegram, salimos fuera
      if (!tg || !tg.initData) {{
        location.replace(fallback);
        return;
      }}

      try {{
        const r = await fetch("/api/session/verify", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ initData: tg.initData }})
        }});
        if (r.ok) {{
          location.replace(next);
        }} else {{
          location.replace(fallback);
        }}
      }} catch (e) {{
        location.replace(fallback);
      }}
    }})();
  </script>
</body>
</html>"""
    return Response(html, mimetype="text/html")


# -------------------- Sesión WebApp (verificación HMAC) --------------------
@web_bp.post("/api/session/verify")
def api_session_verify():
    """
    Front debe enviar {{ initData: Telegram.WebApp.initData }}.
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
            httponly=False,   # accesible por WebView si hicieras comprobaciones en front
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

