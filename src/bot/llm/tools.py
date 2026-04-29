from core.config import settings

# Image configuration
IMAGE_GEN_TOOL = {
  "type": "image_generation",
  "partial_images": 0,
  "output_format": "png",
  "quality": "low",
  "size": "1536x1024",
  "model": settings.image_model,
}

def save_image_locally(b64_data: str, filename: str = "output.png"):
  """Saves a base64 string to a file."""
  import base64
  with open(filename, "wb") as f:
    f.write(base64.b64decode(b64_data))
  return f"Image saved as {filename}"
