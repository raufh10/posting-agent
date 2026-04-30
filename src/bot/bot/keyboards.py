from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def news_review_kb() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup([
    [
      InlineKeyboardButton("✅ Keep", callback_data="news:keep"),
      InlineKeyboardButton("🗑 Drop", callback_data="news:drop"),
    ]
  ])

def draft_pick_kb() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup([
    [
      InlineKeyboardButton("1️⃣", callback_data="draft:0"),
      InlineKeyboardButton("2️⃣", callback_data="draft:1"),
      InlineKeyboardButton("3️⃣", callback_data="draft:2"),
    ]
  ])

def image_review_kb() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup([
    [
      InlineKeyboardButton("✅ Approve", callback_data="image:approve"),
      InlineKeyboardButton("🔄 Redo", callback_data="image:redo"),
    ]
  ])

def confirm_post_kb() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup([
    [
      InlineKeyboardButton("🚀 Post All", callback_data="post:confirm"),
      InlineKeyboardButton("❌ Cancel", callback_data="post:cancel"),
    ]
  ])
