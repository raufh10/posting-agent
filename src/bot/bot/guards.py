from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from core.config import settings

import logging
logger = logging.getLogger(__name__)

def admin_only(func):
  @wraps(func)
  async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
    user_id = update.effective_user.id
    if user_id != settings.admin_user_id:
      logger.warning("Unauthorized access attempt user_id=%s", user_id)
      await update.effective_message.reply_text("⛔ Unauthorized.")
      return
    return await func(update, context, *args, **kwargs)
  return wrapper
