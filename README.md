# imgen-bot

Personal Telegram bot powered by OpenAI Responses API with image generation.

## Stack

- **FastAPI** — webhook server
- **python-telegram-bot** — Telegram integration
- **OpenAI Responses API** — text + image generation (gpt-image-1)

## Project Structure

```
src/bot/
├── api/        # FastAPI webhook endpoint
├── bot/        # Telegram handlers
├── openai/     # OpenAI client and prompts
├── core/       # Config and logging
└── main.py     # App entrypoint
```

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `WEBHOOK_URL` | Web domain + `/webhook` |
| `WEBHOOK_SECRET` | Random secret string |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | e.g. `gpt-image-1` |
| `CHAT_ID` | Your Telegram chat ID |
