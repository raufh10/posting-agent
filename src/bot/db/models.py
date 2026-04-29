from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

class PostStatus(str, Enum):
  unprocessed = "unprocessed"
  posted = "posted"
  dropped = "dropped"

class NewsPost(BaseModel):
  id: UUID
  reddit_id: str | None = None
  subreddit: str
  title: str
  content: str | None = None
  url: str | None = None
  ups: int | None = None
  upvote_ratio: Decimal | None = None
  posted_at: datetime | None = None
  created_at: datetime | None = None
  metadata: dict | None = None
  status: PostStatus | None = None

  class Config:
    from_attributes = True
