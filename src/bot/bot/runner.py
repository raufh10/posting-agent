import asyncio
import logging
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

async def run_generate_draft(item: NewsItem) -> NewsItem:
  prompt = (
    f"Title: {item.original.title}\n"
    f"Content: {item.original.content or ''}\n"
    f"Subreddit: {item.original.subreddit}\n"
    f"Upvotes: {item.original.ups}"
  )
  result = await Runner.run(llm.get_designer(), prompt)
  drafts = result.final_output.draft_options
  item.draft = "\n---\n".join(
    [f"*Option {i+1}*\n{d.intro}\n{d.bridge}\n\n_{d.image_draft}_" for i, d in enumerate(drafts)]
  )
  # store all drafts temporarily for picking
  item.__dict__["_drafts"] = drafts
  return item

async def run_generate_image(item: NewsItem, draft_index: int) -> NewsItem:
  drafts = item.__dict__.get("_drafts", [])
  if not drafts:
    raise ValueError("No drafts found on item")

  chosen = drafts[draft_index]
  prompt = f"{chosen.intro}\n{chosen.bridge}\n{chosen.image_draft}"
  result = await Runner.run(llm.get_artist(), prompt)
  output = result.final_output

  # save image to temp/
  import base64, os
  dir_path = f"temp/{item.id}"
  os.makedirs(dir_path, exist_ok=True)
  image_path = f"{dir_path}/slide.png"
  with open(image_path, "wb") as f:
    f.write(base64.b64decode(output.image_b64))

  item.image_path = image_path
  item.draft = f"{chosen.intro}\n\n{chosen.bridge}"
  return item

async def run_post_all(session: SessionCache, user_id: int) -> list[str]:
  """Posts all approved news items with random delay between each."""
  from cache.session import set_state

  approved = [n for n in session.news if n.image_path and n.draft]
  urns = []

  for i, item in enumerate(approved):
    try:
      urn = await export_news_item(session, item.id)
      urns.append(urn)
      await update_status(item.original.id, PostStatus.posted)
      logger.info("Posted item=%s urn=%s", item.id, urn)
    except Exception as e:
      logger.error("Failed to post item=%s error=%s", item.id, e)
      await update_status(item.original.id, PostStatus.dropped)

    if i < len(approved) - 1:
      delay = random.randint(60, 300)  # 1-5 min
      logger.info("Waiting %ss before next post", delay)
      await asyncio.sleep(delay)

  await set_state(user_id, State.idle)
  return urns
