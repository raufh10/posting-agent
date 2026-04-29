from agents import Agent
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
      output_type=DraftResult
    )

    # Agent 2: The Artist (Focuses on the actual image generation)
    self.artist_agent = Agent(
      name="Visual Artist",
      instructions=ARTIST_SYSTEM_PROMPT,
      model=settings.default_model,
      tools=[IMAGE_GEN_TOOL],
      output_type=ImageResult,
      tool_params={
        "store": True,
        "metadata": {
          "type": "image_generation",
          "retention": "24h"
        }
      }
    )

  def get_designer(self) -> Agent:
    """Returns the agent responsible for creating copy and image drafts."""
    return self.designer_agent

  def get_artist(self) -> Agent:
    """Returns the agent responsible for final image rendering."""
    return self.artist_agent

