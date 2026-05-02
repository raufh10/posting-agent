from agents import Agent, WebSearchTool
from core.config import settings
from llm.tools import IMAGE_GEN_TOOL
from llm.models import DraftResult, ImageResult
from llm.prompts import DESIGNER_SYSTEM_PROMPT, ARTIST_SYSTEM_PROMPT

class LLMClient:
  def __init__(self):
    self.designer_agent = Agent(
      name="Content Designer",
      instructions=DESIGNER_SYSTEM_PROMPT,
      model=settings.default_model,
      tools=[WebSearchTool(search_context_size="medium")],
      output_type=DraftResult
    )

    self.artist_agent = Agent(
      name="Visual Artist",
      instructions=ARTIST_SYSTEM_PROMPT,
      model=settings.default_model,
      tools=[IMAGE_GEN_TOOL],
      output_type=ImageResult
    )

  def get_designer(self) -> Agent:
    """Returns the agent responsible for creating copy and image drafts."""
    return self.designer_agent

  def get_artist(self) -> Agent:
    """Returns the agent responsible for final image rendering."""
    return self.artist_agent
