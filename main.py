import os
import asyncio
import threading
from werkzeug.serving import make_server

from app import create_app
from app.utils.ports import find_free_port
from app.bot.launcher import build_ptb_app
from config import TOKEN, WEBHOOK_URL, WEBHOOK_PATH

def run_flask_in_thread(flask_app, host: str, port: int):
    srv = make_server(host, port, flask_app)
    srv.serve_forever()

async def main():
    web_host = os.getenv("WEB_HOST", "127.0.0.1")
    preferred_port = int(os.getenv("WEB_PORT", "8080"))
    web_port = find_free_port(preferred_port, web_host)
    print(f"[MiniApp] Flask en {web_host}:{web_port} (preferido {preferred_port})")

    # Construye la app de Telegram
    ptb_app = build_ptb_app(TOKEN)

    # Crea Flask e inyecta referencias para el webhook
    flask_app = create_app(ptb_app=ptb_app, webhook_path=WEBHOOK_PATH)

    # Arranca Flask en un hilo (proxy/Nginx hará TLS y proxy-pass a este puerto)
    thread = threading.Thread(target=run_flask_in_thread, args=(flask_app, web_host, web_port), daemon=True)
    thread.start()

    # Inicializa y arranca PTB sin polling (usamos webhook propio)
    await ptb_app.initialize()
    await ptb_app.start()

    # Registra webhook en Telegram
    await ptb_app.bot.set_webhook(url=WEBHOOK_URL)
    print(f"[Webhook] Registrado: {WEBHOOK_URL}")

    try:
        # Mantenerse vivo
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        try:
            # Limpieza
            await ptb_app.bot.delete_webhook(drop_pending_updates=False)
        except Exception:
            pass
        await ptb_app.stop()
        await ptb_app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

