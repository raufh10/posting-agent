from uuid import UUID

from cache.models import NewsItem, SessionCache
from cache.temp import set_session
from export.client import get_person_urn, get_token
from export.uploader import register_image_upload, upload_image
from export.poster import publish_post

async def export_news_item(
  session: SessionCache,
  item_id: UUID,
) -> str:
  """
  Export a single NewsItem from session by its id.
  Uploads image if image_path set and image_urn not yet registered.
  Returns post URN.
  """
  item = next((n for n in session.news if n.id == item_id), None)
  if not item:
    raise ValueError(f"NewsItem {item_id} not found in session")

  token = session.token
  person_urn = session.person_urn

  # Upload image if path exists but urn not yet registered
  if item.image_path and not item.image_urn:
    upload_url, asset_urn = await register_image_upload(token, person_urn)
    await upload_image(upload_url, token, item.image_path)
    item.image_urn = asset_urn
    await set_session(session)

  post_urn = await publish_post(
    token=token,
    person_urn=person_urn,
    text=item.draft,
    asset_urn=item.image_urn,
  )
  return post_urn
