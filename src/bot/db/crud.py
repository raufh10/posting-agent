from datetime import date
from uuid import UUID

from db.client import get_pool
from db.models import NewsPost, PostStatus

async def get_unposted(filter_date: date | None = None) -> list[NewsPost]:
  pool = await get_pool()
  if filter_date:
    rows = await pool.fetch(
      """
      SELECT id, subreddit, title, content, url, ups, upvote_ratio, posted_at
      FROM news_posts
      WHERE status = 'unprocessed'
      AND posted_at::date = $1
      ORDER BY posted_at ASC
      """,
      filter_date,
    )
  else:
    rows = await pool.fetch(
      """
      SELECT id, subreddit, title, content, url, ups, upvote_ratio, posted_at
      FROM news_posts
      WHERE status = 'unprocessed'
      ORDER BY posted_at ASC
      """
    )
  return [NewsPost(**dict(row)) for row in rows]

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
  return NewsPost(**dict(row)) if row else None
