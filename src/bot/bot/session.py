from datetime import date, timedelta
from uuid import uuid4

from cache.models import NewsItem, SessionCache
from cache.temp import get_session, set_session
from db.crud import get_unposted
from export.client import get_person_urn, get_token

async def init_session() -> SessionCache:
  yesterday = date.today() - timedelta(days=1)

  existing = await get_session(yesterday)
  if existing:
    return existing

  posts = await get_unposted(filter_date=yesterday)
  news = [
    NewsItem(
      id=uuid4(),
      original=post,
      draft="",
    )
    for post in posts
  ]

  session = SessionCache(
    date=yesterday,
    person_urn=get_person_urn(),
    token=get_token(),
    news=news,
  )
  await set_session(session)
  return session

async def save_session(session: SessionCache) -> None:
  await set_session(session)
