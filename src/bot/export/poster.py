import httpx
from export.client import LINKEDIN_API

def _headers(token: str) -> dict:
  return {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0",
  }

def _build_body(
  person_urn: str,
  text: str,
  asset_urn: str | None = None,
) -> dict:
  body: dict = {
    "author": person_urn,
    "lifecycleState": "PUBLISHED",
    "specificContent": {
      "com.linkedin.ugc.ShareContent": {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "IMAGE" if asset_urn else "NONE",
      }
    },
    "visibility": {
      "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    },
  }

  if asset_urn:
    body["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
      {
        "status": "READY",
        "media": asset_urn,
      }
    ]

  return body

async def publish_post(
  token: str,
  person_urn: str,
  text: str,
  asset_urn: str | None = None,
) -> str:
  async with httpx.AsyncClient() as client:
    r = await client.post(
      f"{LINKEDIN_API}/ugcPosts",
      headers=_headers(token),
      json=_build_body(person_urn, text, asset_urn),
    )
    r.raise_for_status()
    return r.headers.get("x-restli-id", "")
