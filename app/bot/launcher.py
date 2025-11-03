import asyncio
from telegram.ext import (
    ApplicationBuilder, AIORateLimiter, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters, ContextTypes
)
from telegram.request import HTTPXRequest
from telegram.error import TimedOut as TgTimedOut
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.constants import ChatType

# /start: abre la MiniApp con URL FIJA (sin ?chat_id)
async def cmd_start(update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    base_url = context.bot_data.get("miniapp_url") or "https://example.com"

    if chat.type == ChatType.PRIVATE:
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🧩 Abrir Mini App", web_app=WebAppInfo(url=base_url))]]
        )
    else:
        kb = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🧩 Abrir Mini App", url=base_url)]]
        )

    await update.effective_message.reply_text(
        "Abre la Mini App para gestionar números y ver estadísticas:",
        reply_markup=kb
    )

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

