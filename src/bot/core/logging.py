import logging
import sys
from bot.core.config import settings

def setup_logging() -> None:
  level = logging.DEBUG if settings.debug else logging.INFO

  logging.basicConfig(
    level=level,
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
      logging.StreamHandler(sys.stdout),
    ],
  )

  # Set third-party loggers level to WARNING
  logging.getLogger("httpx").setLevel(logging.WARNING)
  logging.getLogger("httpcore").setLevel(logging.WARNING)
  logging.getLogger("telegram").setLevel(logging.WARNING)
