# app/bot/launcher.py
import asyncio
from telegram.ext import (
    ApplicationBuilder, AIORateLimiter, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters, ContextTypes
)
from telegram.request import HTTPXRequest
from telegram.error import TimedOut as TgTimedOut


# /start: solo mensaje de bienvenida (sin teclados ni enlaces)
async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "¡Bienvenido! 👋\n\n"
        "Usa la **Mini App** para añadir tiradas y ver estadísticas.\n"
        "➡️ Ábrela desde el **botón del menú del bot** (junto al campo de escritura)."
    )
    await update.effective_message.reply_text(
        text,
        disable_web_page_preview=True
    )


# Opcional: si la Mini App envía datos con WebApp.sendData (no hacemos nada aquí)
async def web_app_data(update, context: ContextTypes.DEFAULT_TYPE):
    return


def build_ptb_app(token: str):
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=60.0, http_version="1.1")
    app = (
        ApplicationBuilder()
        .token(token)
        .request(request)
        .rate_limiter(AIORateLimiter(
            overall_max_rate=30, overall_time_period=1.0,
            group_max_rate=18, group_time_period=60
        ))
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))

    # Deja el CallbackQueryHandler por si en el futuro añades callbacks
    app.add_handler(CallbackQueryHandler(lambda *_: None))
    return app


async def run_ptb(application):
    attempt = 0
    while True:
        try:
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            break
        except (TgTimedOut, asyncio.TimeoutError) as e:
            attempt += 1
            delay = min(5 * attempt, 30)
            print(f"[Bot] Timeout al iniciar (intento {attempt}). Reintentando en {delay}s… ({e})")
            await asyncio.sleep(delay)
        except Exception as e:
            attempt += 1
            delay = min(5 * attempt, 30)
            print(f"[Bot] Error al iniciar (intento {attempt}): {e}. Reintentando en {delay}s…")
            await asyncio.sleep(delay)

    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass

    try:
        await application.updater.stop()
    finally:
        await application.stop()
        await application.shutdown()

