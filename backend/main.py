import asyncio
import os
from aiohttp import web

from app.bot.launcher import build_ptb_app, run_ptb
from config import MODE, PUBLIC_URL, TOKEN, WEBHOOK_SECRET

WEBHOOK_PATH = "/telegram/webhook"


async def _run_webhook(application, host: str, port: int, webhook_url: str, secret_token: str) -> None:
    attempt = 0
    while True:
        try:
            await application.initialize()
            await application.start()

            if application.web_app:
                async def health(_request: web.Request) -> web.Response:
                    return web.Response(text="ok\n", content_type="text/plain")

                application.web_app.router.add_get("/health", health)

            await application.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token,
                drop_pending_updates=True,
            )

            await application.updater.start_webhook(
                listen=host,
                port=port,
                url_path=WEBHOOK_PATH.lstrip("/"),
                webhook_url=None,
                secret_token=secret_token,
            )
            print(f"[Bot] Webhook escuchando en http://{host}:{port}{WEBHOOK_PATH} -> {webhook_url}")
            break
        except Exception as exc:  # pragma: no cover - solo logs
            attempt += 1
            delay = min(5 * attempt, 30)
            print(f"[Bot] Error al iniciar webhook (intento {attempt}): {exc}. Reintentando en {delay}s…")
            await asyncio.sleep(delay)

    try:
        await asyncio.Future()
    except asyncio.CancelledError:  # pragma: no cover - parada ordenada
        pass
    finally:
        try:
            await application.bot.delete_webhook(drop_pending_updates=False)
        except Exception:  # pragma: no cover - mejor esfuerzo
            pass
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


async def main() -> None:
    mode = MODE.lower()
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = _env_int("WEB_PORT", 8080)

    application = build_ptb_app(TOKEN)

    if mode == "webhook":
        webhook_url = f"{PUBLIC_URL.rstrip('/')}{WEBHOOK_PATH}"
        await _run_webhook(application, host, port, webhook_url, WEBHOOK_SECRET)
    else:
        await run_ptb(application)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # pragma: no cover - parada manual
        pass
