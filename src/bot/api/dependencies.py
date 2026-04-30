from fastapi import HTTPException, Request
from core.config import settings

async def verify_webhook_secret(request: Request) -> None:
  token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
  if token != settings.WEBHOOK_SECRET:
    raise HTTPException(status_code=403, detail="Invalid secret token")
