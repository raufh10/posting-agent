import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from telegram import Update
from telegram.ext import Application, MessageHandler, filters

from bot.api.router import router
from bot.core.config import settings
from bot.core.logging import setup_logging
from bot.bot.handlers import handle_message

setup_logging()
logger = logging.getLogger(__name__)

def build_bot_app() -> Application:

  app = (
    Application.builder()
    .token(settings.telegram_bot_token)
    .build()
  )

  chat_filter = filters.Chat(chat_id=settings.chat_id)

  app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND & chat_filter, handle_message)
  )

  return app

@asynccontextmanager
async def lifespan(app: FastAPI):
  bot_app = build_bot_app()
  await bot_app.initialize()
  await bot_app.bot.set_webhook(
    url=settings.webhook_url,
    secret_token=settings.webhook_secret,
  )
  app.state.bot_app = bot_app
  logger.info("Bot started, webhook set to %s", settings.webhook_url)

  yield

  await bot_app.bot.delete_webhook()
  await bot_app.shutdown()
  logger.info("Bot stopped")

app = FastAPI(lifespan=lifespan)
app.include_router(router)
