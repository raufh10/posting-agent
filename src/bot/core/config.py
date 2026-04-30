from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
  )

  # Bot
  telegram_bot_token: str
  webhook_url: str
  webhook_secret: str
  admin_user_id: int

  # LinkedIn
  person_id: str
  token: str

  # OpenAI
  openai_api_key: str
  default_model: str
  image_model: str

  # Database
  database_url: str
  redis_url: str

  # Server
  host: str = "0.0.0.0"
  port: int = 8000

  # Environment
  environment: str = "development"

  @property
  def is_production(self) -> bool:
    return self.environment == "production"

settings = Settings()
