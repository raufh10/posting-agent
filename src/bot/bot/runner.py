import asyncio
import base64
import logging
import os
import random
from uuid import UUID

from agents import Runner

from bot.states import State
from cache.models import NewsItem, SessionCache
from cache.session import set_state
from cache.temp import set_session
from db.crud import update_status
from db.models import PostStatus
from export.service import export_news_item
from llm import LLMClient

logger = logging.getLogger(__name__)
llm = LLMClient()

def _get_field(obj, key):
  if isinstance(obj, dict):
    return obj.get(key)
  return getattr(obj, key, None)

async def run_generate_draft(item: NewsItem) -> NewsItem:
  prompt = (
    f"Title: {item.original.title}\n"
    f"Content: {item.original.content or ''}\n"
    f"Subreddit: {item.original.subreddit}\n"
    f"Upvotes: {item.original.ups}"
  )
  result = await Runner.run(llm.get_designer(), prompt)
  drafts = result.final_output.draft_options
  item.drafts = drafts

  header = (
    f"📰 <b>{item.original.title}</b>\n"
    f"<i>{item.original.content[:200] + '...' if item.original.content and len(item.original.content) > 200 else item.original.content or ''}</i>\n"
    f"\n"
  )

  item.draft = header + "\n---\n".join(
    [f"<b>Option {i+1}</b>\n{d.intro}\n{d.bridge}\n\n<i>{d.image_draft}</i>" for i, d in enumerate(drafts)]
  )
  return item

async def run_generate_draft(item: NewsItem) -> NewsItem:
  prompt = (
    f"Title: {item.original.title}\n"
    f"Content: {item.original.content or ''}\n"
    f"Subreddit: {item.original.subreddit}\n"
    f"Upvotes: {item.original.ups}"
  )
  result = await Runner.run(llm.get_designer(), prompt)
  drafts = result.final_output.draft_options
  item.drafts = drafts

  permalink = None
  if item.original.metadata and isinstance(item.original.metadata, dict):
    permalink = item.original.metadata.get("permalink")
  source = f"https://reddit.com{permalink}" if permalink else item.original.url or ""

  header = (
    f"📰 <b>{item.original.title}</b>\n"
    f"<i>{item.original.content[:200] + '...' if item.original.content and len(item.original.content) > 200 else item.original.content or ''}</i>\n"
    f"🔗 Source: {source}\n"
    f"\n"
  )

  item.draft = header + "\n---\n".join(
    [f"<b>Option {i+1}</b>\n{d.intro}\n{d.bridge}\n\n<i>{d.image_draft}</i>" for i, d in enumerate(drafts)]
  )
  return item

async def run_generate_image(item: NewsItem, draft_index: int) -> NewsItem:
  if not item.drafts:
    raise ValueError("No drafts found on item")

  chosen = item.drafts[draft_index]
  prompt = f"{chosen.intro}\n{chosen.bridge}\n{chosen.image_draft}"
  result = await Runner.run(llm.get_artist(), prompt)

  # extract image
  image_b64: str | None = None
  for new_item in result.new_items:
    if _get_field(new_item, "type") != "tool_call_item":
      continue
    raw = _get_field(new_item, "raw_item")
    if _get_field(raw, "type") != "image_generation_call":
      continue
    img = _get_field(raw, "result")
    if isinstance(img, str) and img:
      image_b64 = img
      break

  if not image_b64:
    raise ValueError("Agent returned no image data")

  dir_path = f"temp/{item.id}"
  os.makedirs(dir_path, exist_ok=True)
  image_path = f"{dir_path}/slide.png"

  with open(image_path, "wb") as f:
    f.write(base64.b64decode(image_b64))

  logger.info("Image saved to %s size=%s", image_path, os.path.getsize(image_path))

  permalink = None
  if item.original.metadata and isinstance(item.original.metadata, dict):
    permalink = item.original.metadata.get("permalink")
  source = f"https://reddit.com{permalink}" if permalink else item.original.url or ""

  item.image_path = image_path
  item.draft = f"{chosen.intro}\n\n{chosen.bridge}\n\n🔗 Source: {source}"
  return item

async def run_post_all(session: SessionCache, user_id: int) -> list[str]:
  approved = [n for n in session.news if n.image_path and n.draft]
  urns = []

  for i, item in enumerate(approved):
    try:
      urn = await export_news_item(session, item.id)
      urns.append(urn)
      await update_status(item.original.id, PostStatus.posted)
      logger.info("Posted item=%s urn=%s", item.id, urn)

      _cleanup_temp(item)

    except Exception as e:
      logger.error("Failed to post item=%s error=%s", item.id, e)
      await update_status(item.original.id, PostStatus.dropped)

    if i < len(approved) - 1:
      delay = random.randint(60, 300)
      logger.info("Waiting %ss before next post", delay)
      await asyncio.sleep(delay)

  await set_state(user_id, State.idle)
  return urns

def _cleanup_temp(item: NewsItem) -> None:
  import shutil
  dir_path = f"temp/{item.id}"
  if os.path.exists(dir_path):
    shutil.rmtree(dir_path)
    logger.info("Cleaned temp dir %s", dir_path)
