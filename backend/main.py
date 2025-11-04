import asyncio
import os
from typing import Optional
from urllib.parse import urlparse

from aiohttp import web
from telegram import Update

from app.bot.launcher import build_ptb_app, run_ptb
from config import MODE, TOKEN, WEBHOOK_SECRET, WEBHOOK_URL


def _webhook_path_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/telegram/webhook"
    if not path.startswith("/"):
        path = f"/{path}"
    return path


WEBHOOK_PATH = _webhook_path_from_url(WEBHOOK_URL)


async def _stop_application(application) -> None:
    try:
        await application.stop()
    except Exception:  # pragma: no cover - mejor esfuerzo
        pass
    try:
        await application.shutdown()
    except Exception:  # pragma: no cover - mejor esfuerzo
        pass


async def _cleanup_site(site: Optional[web.BaseSite], runner: Optional[web.AppRunner]) -> None:
    if site is not None:
        try:
            await site.stop()
        except Exception:  # pragma: no cover - mejor esfuerzo
            pass
    if runner is not None:
        try:
            await runner.cleanup()
        except Exception:  # pragma: no cover - mejor esfuerzo
            pass


async def _run_webhook(application, host: str, port: int, webhook_url: str, secret_token: str) -> None:
    attempt = 0
    runner: Optional[web.AppRunner] = None
    site: Optional[web.BaseSite] = None

    while True:
        try:
            await application.initialize()
            await application.start()

            webhook_app = web.Application()

            async def health(_request: web.Request) -> web.Response:
                return web.Response(text="ok\n", content_type="text/plain")

            async def telegram_webhook(request: web.Request) -> web.Response:
                if secret_token:
                    header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
                    if header != secret_token:
                        return web.Response(status=403)

                if request.method != "POST":
                    return web.Response(status=405)

                try:
                    data = await request.json()
                except Exception:
                    return web.Response(status=400)

                try:
                    update = Update.de_json(data, application.bot)
                except Exception:
                    return web.Response(status=400)

                await application.update_queue.put(update)
                return web.Response(text="ok")

            webhook_app.router.add_get("/health", health)
            webhook_app.router.add_post(WEBHOOK_PATH, telegram_webhook)

            runner = web.AppRunner(webhook_app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            await site.start()

            await application.bot.set_webhook(
                url=webhook_url,
                secret_token=secret_token or None,
                drop_pending_updates=(attempt == 0),
            )

            print(f"[Bot] Webhook escuchando en http://{host}:{port}{WEBHOOK_PATH} -> {webhook_url}")
            break
        except Exception as exc:  # pragma: no cover - solo logs
            attempt += 1
            delay = min(5 * attempt, 30)
            print(f"[Bot] Error al iniciar webhook (intento {attempt}): {exc}. Reintentando en {delay}s…")
            await _cleanup_site(site, runner)
            site = None
            runner = None
            await _stop_application(application)
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
        await _cleanup_site(site, runner)
        await _stop_application(application)


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
        await _run_webhook(application, host, port, WEBHOOK_URL, WEBHOOK_SECRET)
    else:
        await run_ptb(application)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:  # pragma: no cover - parada manual
        pass
