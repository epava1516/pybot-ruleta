import os
import asyncio
import threading
from app import create_app
from app.utils.ports import find_free_port
from app.bot.launcher import build_ptb_app, run_ptb
from config import TOKEN, DOMAIN, MODE, PUBLIC_URL, WEBHOOK_SECRET, ENVIRONMENT

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
    print(f"[Bot] MODE={MODE}")

    ptb_app = build_ptb_app(TOKEN)
    # URL pública para el botón /start (MiniApp)
    ptb_app.bot_data["miniapp_url"] = f"{PUBLIC_URL}/"

    if MODE == "webhook":
        # 1) Arranca Flask en hilo (sirve MiniApp + endpoint webhook)
        #    Le pasamos PTB_APP, su loop y el secreto del webhook.
        loop = asyncio.get_running_loop()
        flask_app = create_app(ptb_app=ptb_app, webhook_secret=WEBHOOK_SECRET, ptb_loop=loop)
        thread = threading.Thread(target=run_flask_in_thread, args=(flask_app, web_host, web_port), daemon=True)
        thread.start()

        # 2) Inicializa PTB sin polling y fija el webhook
        await ptb_app.initialize()
        await ptb_app.start()

        webhook_url = f"{PUBLIC_URL}/telegram/webhook"
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        print(f"[Bot] Webhook activo en {webhook_url}")

        try:
            # Mantener el proceso vivo
            await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await ptb_app.bot.delete_webhook()
            except Exception:
                pass
            await ptb_app.stop()
            await ptb_app.shutdown()

    else:
        # POLLING clásico (Flask solo para MiniApp)
        flask_app = create_app()
        thread = threading.Thread(target=run_flask_in_thread, args=(flask_app, web_host, web_port), daemon=True)
        thread.start()
        await run_ptb(ptb_app)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

