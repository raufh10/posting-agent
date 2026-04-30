from enum import Enum, auto

class State(str, Enum):
  idle = "idle"
  reviewing_news = "reviewing_news"
  generating_drafts = "generating_drafts"
  picking_draft = "picking_draft"
  generating_image = "generating_image"
  reviewing_image = "reviewing_image"
  posting = "posting"
