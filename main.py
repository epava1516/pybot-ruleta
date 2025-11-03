import os
import asyncio
import threading
from app import create_app
from app.utils.ports import find_free_port
from app.bot.launcher import build_ptb_app, run_ptb
from config import TOKEN, DOMAIN, MODE, PUBLIC_URL, WEBHOOK_SECRET, ENVIRONMENT
from telegram import MenuButtonWebApp, WebAppInfo

def run_flask_in_thread(flask_app, host: str, port: int):
    from werkzeug.serving import make_server
    srv = make_server(host, port, flask_app)
    srv.serve_forever()

async def _ensure_menu_button(bot, url: str):
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Abrir Mini App", web_app=WebAppInfo(url=url))
        )
        print(f"[Bot] Menu Button configurado -> {url}")
    except Exception as e:
        print(f"[Bot] No se pudo configurar el Menu Button: {e}")

async def main():
    web_host = os.getenv("WEB_HOST", "0.0.0.0")
    preferred_port = int(os.getenv("WEB_PORT", "8080"))
    web_port = find_free_port(preferred_port, web_host)
    print(f"[MiniApp] Flask en {web_host}:{web_port} (preferido {preferred_port})")
    print(f"[MiniApp] Dominio configurado: {DOMAIN}")
    print(f"[Bot] MODE={MODE}")

    ptb_app = build_ptb_app(TOKEN)

    # 👉 Menú y /start apuntan al gate (redirige a '/' tras verificar cookie)
    miniapp_url = f"{PUBLIC_URL}/gate?next=/"
    ptb_app.bot_data["miniapp_url"] = miniapp_url

    if MODE == "webhook":
        loop = asyncio.get_running_loop()
        flask_app = create_app(ptb_app=ptb_app, webhook_secret=WEBHOOK_SECRET, ptb_loop=loop)
        thread = threading.Thread(target=run_flask_in_thread, args=(flask_app, web_host, web_port), daemon=True)
        thread.start()

        await ptb_app.initialize()
        await ptb_app.start()
        await _ensure_menu_button(ptb_app.bot, miniapp_url)

        webhook_url = f"{PUBLIC_URL}/telegram/webhook"
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True,
        )
        print(f"[Bot] Webhook activo en {webhook_url}")

        try:
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
        flask_app = create_app()
        thread = threading.Thread(target=run_flask_in_thread, args=(flask_app, web_host, web_port), daemon=True)
        thread.start()
        await run_ptb(ptb_app)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

