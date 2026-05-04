import json
from datetime import date
from uuid import UUID

from db.client import get_pool
from db.models import NewsPost, PostStatus

def _parse_row(row) -> NewsPost:
  data = dict(row)
  if isinstance(data.get("metadata"), str):
    data["metadata"] = json.loads(data["metadata"])
  return NewsPost(**data)

async def get_unposted() -> list[NewsPost]:
  pool = await get_pool()
  rows = await pool.fetch(
    """
    SELECT id, subreddit, title, content, url, ups, upvote_ratio, posted_at, metadata
    FROM news_posts
    WHERE status = 'unprocessed'
    AND ups >= 50
    AND posted_at >= NOW() - INTERVAL '24 hours'
    ORDER BY ups DESC
    """
  )
  return [_parse_row(row) for row in rows]

async def update_status(post_id: UUID, status: PostStatus) -> NewsPost | None:
  pool = await get_pool()
  row = await pool.fetchrow(
    """
    UPDATE news_posts
    SET status = $1
    WHERE id = $2
    RETURNING *
    """,
    status.value,
    post_id,
  )
  return _parse_row(row) if row else None
