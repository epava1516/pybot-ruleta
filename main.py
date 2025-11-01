import os
import asyncio
import threading
from app import create_app
from app.utils.ports import find_free_port
from app.bot.launcher import build_ptb_app, run_ptb
from config import TOKEN, DOMAIN, WEBHOOK_URL  # DOMAIN se usa para logs y coherencia

def run_flask_in_thread(flask_app, host: str, port: int):
    from werkzeug.serving import make_server
    srv = make_server(host, port, flask_app)
    srv.serve_forever()

async def main():
    # Escuchar en 0.0.0.0 cuando se ejecuta en contenedor
    web_host = os.getenv("WEB_HOST", "0.0.0.0")
    preferred_port = int(os.getenv("WEB_PORT", "8080"))
    web_port = find_free_port(preferred_port, web_host)
    print(f"[MiniApp] Flask en {web_host}:{web_port} (preferido {preferred_port})")
    print(f"[MiniApp] Dominio configurado: {DOMAIN}")

    flask_app = create_app()
    thread = threading.Thread(target=run_flask_in_thread, args=(flask_app, web_host, web_port), daemon=True)
    thread.start()

    # El bot sigue con **polling** (no usamos webhooks, ni túneles).
    ptb_app = build_ptb_app(TOKEN)

    # La MiniApp se servirá detrás de Nginx por tu dominio.
    # Para que /start abra la MiniApp correcta, inyectamos la URL pública
    # que expondrá el proxy: https://{DOMAIN}/
    ptb_app.bot_data["miniapp_url"] = f"https://{DOMAIN}/"

    bot_task = asyncio.create_task(run_ptb(ptb_app))
    try:
        await bot_task
    finally:
        bot_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

