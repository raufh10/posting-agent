from core.config import settings

LINKEDIN_API = "https://api.linkedin.com/v2"

def get_person_urn() -> str:
  return f"urn:li:person:{settings.person_id}"

def get_token() -> str:
  return settings.token
