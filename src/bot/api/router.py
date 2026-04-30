import logging

from fastapi import APIRouter, Depends, Request
from telegram import Update
from telegram.ext import Application

from api.dependencies import verify_webhook_secret

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook", dependencies=[Depends(verify_webhook_secret)])
async def webhook(request: Request) -> dict:
  app: Application = request.app.state.bot_app
  data = await request.json()
  update = Update.de_json(data, app.bot)
  await app.process_update(update)
  return {"ok": True}
