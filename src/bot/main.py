import os
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

from api import router
from bot import cmd_cancel, cmd_start, cmd_status, handle_callback
from cache.client import close_redis, get_redis
from core.config import settings
from db.client import close_pool, get_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _build_bot_app():
  app = ApplicationBuilder().token(settings.telegram_bot_token).build()
  app.add_handler(CommandHandler("start", cmd_start))
  app.add_handler(CommandHandler("status", cmd_status))
  app.add_handler(CommandHandler("cancel", cmd_cancel))
  app.add_handler(CallbackQueryHandler(handle_callback))
  return app

@asynccontextmanager
async def lifespan(app: FastAPI):
  await get_pool()
  await get_redis()

  bot_app = _build_bot_app()
  await bot_app.initialize()

  if settings.is_production:
    await bot_app.bot.set_webhook(
      url=f"{settings.webhook_url}/webhook",
      secret_token=settings.webhook_secret,
    )
    logger.info("Webhook set: %s/webhook", settings.webhook_url)
  else:
    await bot_app.bot.delete_webhook()
    await bot_app.start()
    await bot_app.updater.start_polling()
    logger.info("Polling mode active")

  app.state.bot_app = bot_app

  yield

  if not settings.is_production:
    await bot_app.updater.stop()
    await bot_app.stop()

  await bot_app.shutdown()
  await close_pool()
  await close_redis()

app = FastAPI(lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
  os.makedirs("temp", exist_ok=True)

  uvicorn.run(
    "main:app",
    host=settings.host,
    port=settings.port,
    reload=not settings.is_production,
  )
