import logging
from openai import AsyncOpenAI
from bot.core.config import settings
from bot.openai.prompts import SYSTEM_PROMPT, PROMPT_CACHE_KEY

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)

IMAGE_TOOL = {
  "type": "image_generation",
  "partial_images": 0,
  "output_format": "png",
  "quality": "medium",
  "size": "1536x1024",
  "background": "opaque",
  "moderation": "auto",
}

async def get_response(user_message: str) -> dict:
  logger.info("OpenAI request | message='%s'", user_message[:80])

  response = await client.responses.create(
    model=settings.openai_model,
    instructions=SYSTEM_PROMPT,
    input=user_message,
    tools=[IMAGE_TOOL],
    store=True,
    metadata={
      "prompt_cache_key": PROMPT_CACHE_KEY,
      "prompt_cache_retention": "24h",
    },
  )

  logger.debug("OpenAI raw response id=%s model=%s", response.id, response.model)

  result = {"text": None, "image_b64": None}

  for item in response.output:
    if item.type == "message":
      for block in item.content:
        if block.type == "output_text":
          result["text"] = block.text
          logger.debug("Text output | chars=%d", len(block.text))

    elif item.type == "image_generation_call":
      result["image_b64"] = item.result
      logger.info("Image generated | size=%s quality=%s",
        IMAGE_TOOL["size"],
        IMAGE_TOOL["quality"],
      )

  if not result["text"] and not result["image_b64"]:
    logger.warning("Empty response from OpenAI | response_id=%s", response.id)

  logger.info("OpenAI response | text=%s image=%s",
    bool(result["text"]),
    bool(result["image_b64"]),
  )

  return result
