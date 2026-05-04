import os
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.guards import admin_only
from bot.keyboards import (
  confirm_post_kb,
  draft_pick_kb,
  image_review_kb,
  news_review_kb,
)
from bot.runner import run_generate_draft, run_generate_image, run_post_all
from bot.session import init_session, save_session
from bot.states import State
from cache.session import clear_state, get_state, set_state
from cache.temp import clear_session, get_session
from db.crud import update_status
from db.models import PostStatus

logger = logging.getLogger(__name__)

# ── helpers ────────────────────────────────────────────────────────────────
async def _get_current_item(session, user_id: int):
  """Returns first news item not yet drafted."""
  return next((n for n in session.news if not n.draft), None)

# ── commands ───────────────────────────────────────────────────────────────
@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  session = await init_session()

  if not session.news:
    await update.message.reply_text("📭 No unprocessed news for yesterday.")
    return

  await set_state(user_id, State.reviewing_news)
  context.user_data["news_index"] = 0
  await _send_news_item(update.message, session, 0)

async def _send_news_item(message, session, index: int) -> None:
  item = session.news[index]
  post = item.original
  total = len(session.news)

  permalink = None
  if post.metadata and isinstance(post.metadata, dict):
    permalink = post.metadata.get("permalink")

  reddit_url = f"https://reddit.com{permalink}" if permalink else post.url or ""
  reddit_url = f"{post.metadata}"

  text = (
    f"📰 <b>{index+1}/{total}</b>\n\n"
    f"<b>{post.title}</b>\n\n"
    f"r/{post.subreddit} · ⬆️ {post.ups}\n"
    f"{post.content[:200] if post.content else ''}\n\n"
    f"{reddit_url}"
    #f"🔗 <a href='{reddit_url}'>View on Reddit</a>"
  )
  await message.reply_text(
    text,
    parse_mode="HTML",
    reply_markup=news_review_kb()
  )

@admin_only
async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  state = await get_state(user_id) or State.idle
  await update.message.reply_text(f"Current state: `{state}`", parse_mode="Markdown")

@admin_only
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  import shutil

  session = await get_session()
  if session:
    for item in session.news:
      dir_path = f"temp/{item.id}"
      if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    await clear_session()

  await clear_state(user_id)
  await update.message.reply_text("🛑 Session cancelled.")

# ── callbacks ──────────────────────────────────────────────────────────────
@admin_only
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  query = update.callback_query
  await query.answer()

  user_id = update.effective_user.id
  state = await get_state(user_id)
  data = query.data

  session = await get_session()
  if not session:
    await query.edit_message_text("⚠️ No active session. Run /start first.")
    return

  # ── news review ──
  if data.startswith("news:") and state == State.reviewing_news:
    index = context.user_data.get("news_index", 0)
    item = session.news[index]

    if data == "news:drop":
      await update_status(item.original.id, PostStatus.dropped)
      session.news.pop(index)
      await save_session(session)
      await query.edit_message_text("🗑 Dropped.")
    else:
      index += 1
      context.user_data["news_index"] = index

    if index < len(session.news):
      await _send_news_item(query.message, session, index)
    else:
      await set_state(user_id, State.generating_drafts)
      await query.message.reply_text(
        f"✅ {len(session.news)} items kept. Generating drafts...",
      )
      await _generate_next_draft(query.message, session, user_id, context)

  # ── draft picking ──
  elif data.startswith("draft:") and state == State.picking_draft:
    draft_index = int(data.split(":")[1])
    item_id = context.user_data.get("current_item_id")
    item = next((n for n in session.news if str(n.id) == item_id), None)

    if not item:
      await query.edit_message_text("⚠️ Item not found.")
      return

    context.user_data["draft_index"] = draft_index

    await query.edit_message_text(f"🎨 Generating image for option {draft_index+1}...")
    await set_state(user_id, State.generating_image)

    item = await run_generate_image(item, draft_index)
    for i, n in enumerate(session.news):
      if n.id == item.id:
        session.news[i] = item
    await save_session(session)

    await _send_image_review(query.message, item, user_id)

  # ── image review ──
  elif data.startswith("image:") and state == State.reviewing_image:
    item_id = context.user_data.get("current_item_id")
    item = next((n for n in session.news if str(n.id) == item_id), None)

    if data == "image:redo":
      await query.message.reply_text("🔄 Regenerating image...")
      draft_index = context.user_data.get("draft_index", 0)  # now always correct
      item = await run_generate_image(item, draft_index)
      for i, n in enumerate(session.news):
        if n.id == item.id:
          session.news[i] = item
      await save_session(session)
      await _send_image_review(query.message, item, user_id)

    elif data == "image:approve":
      await query.message.reply_text("✅ Image approved.")
      await set_state(user_id, State.generating_drafts)
      await _generate_next_draft(query.message, session, user_id, context)

  # ── posting ──
  elif data.startswith("post:") and state == State.posting:
    if data == "post:confirm":
      await query.edit_message_text("🚀 Posting with random delays (1–5 min)...")
      urns = await run_post_all(session, user_id)
      await clear_session()
      await query.message.reply_text(
        f"✅ Posted {len(urns)} item(s) to LinkedIn."
      )
    elif data == "post:cancel":
      await clear_state(user_id)
      await query.edit_message_text("❌ Posting cancelled.")

# ── internal flow helpers ──────────────────────────────────────────────────
async def _generate_next_draft(message, session, user_id: int, context) -> None:
  item = await _get_current_item(session, user_id)

  if not item:
    # all items drafted — move to posting
    await set_state(user_id, State.posting)
    await message.reply_text(
      f"✅ All drafts ready. Ready to post {len(session.news)} item(s)?",
      reply_markup=confirm_post_kb(),
    )
    return

  await set_state(user_id, State.generating_drafts)
  await message.reply_text(
    f"✍️ Generating drafts for:\n<b>{item.original.title}</b>",
    parse_mode="HTML",
  )

  item = await run_generate_draft(item)
  for i, n in enumerate(session.news):
    if n.id == item.id:
      session.news[i] = item
  await save_session(session)

  context.user_data["current_item_id"] = str(item.id)
  await set_state(user_id, State.picking_draft)

  await message.reply_text(
    f"📝 Pick a draft:\n\n{item.draft}",
    parse_mode="HTML",
    reply_markup=draft_pick_kb(),
  )

async def _send_image_review(message, item, user_id: int) -> None:
  from telegram import InputFile
  import os

  await set_state(user_id, State.reviewing_image)

  with open(item.image_path, "rb") as f:
    await message.reply_photo(
      photo=InputFile(f, filename="slide.png"),
      caption=f"🖼 Generated image\n\n_{item.draft[:200]}..._",
      parse_mode="Markdown",
      reply_markup=image_review_kb(),
    )
