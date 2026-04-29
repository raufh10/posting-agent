from pydantic import BaseModel, Field
from typing import List, Optional

class Draft(BaseModel):
  intro: str = Field(..., description="The opening hook or introduction text")
  bridge: str = Field(..., description="The connective tissue linking the intro to the visual")
  image_draft: str = Field(..., description="The prompt for the image, including specific news copy or text to be rendered inside the visual")

class DraftResult(BaseModel):
  draft_options: List[Draft] = Field(
    ..., 
    max_length=3, 
    description="A list of up to 3 distinct draft variations"
  )
  explanation: str = Field(
    ..., 
    description="A single sentence explaining the adjustments or logic applied by the AI"
  )

class ImageResult(BaseModel):
  image_b64: str = Field(..., description="The base64 encoded string of the generated image")
  image_copy: str = Field(..., description="The specific text, headline, or news copy displayed within the image")
  explanation: str = Field(
    ..., 
    description="A single sentence explaining the adjustments or logic applied by the AI"
  )

