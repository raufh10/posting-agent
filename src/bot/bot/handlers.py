import logging
import base64
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from bot.openai.client import get_response

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  message = update.message

  if not message or not message.text:
    return

  user_id = message.from_user.id
  text = message.text

  logger.info("Message from user_id=%s", user_id)

  await message.chat.send_action("typing")

  try:
    result = await get_response(text)

    if result["image_b64"]:
      image_bytes = BytesIO(base64.b64decode(result["image_b64"]))
      image_bytes.name = "image.png"
      await message.reply_photo(
        photo=image_bytes,
        caption=result["text"],
      )

    elif result["text"]:
      await message.reply_text(result["text"])

    else:
      await message.reply_text("Sorry, I couldn't generate a response.")

  except Exception as e:
    logger.error("Failed to handle message user_id=%s error=%s", user_id, e)
    await message.reply_text("Something went wrong, please try again.")
