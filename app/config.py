import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = BASE_DIR / ".env"
load_dotenv(DOTENV_PATH)

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_ID_STR: str = os.getenv("ALLOWED_USER_ID", "").strip()

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN.startswith("your_") or "bot_token_here" in TELEGRAM_BOT_TOKEN.lower():
    raise ValueError(
        "Missing or invalid TELEGRAM_BOT_TOKEN. "
        "Update .env with your real Telegram bot token."
    )

if not ALLOWED_USER_ID_STR:
    raise ValueError(
        "Missing ALLOWED_USER_ID. "
        "Update .env with your numeric Telegram user ID."
    )

ALLOWED_USER_IDS = [
    int(value.strip())
    for value in ALLOWED_USER_ID_STR.replace(",", " ").split()
    if value.strip().isdigit()
]

if not ALLOWED_USER_IDS:
    raise ValueError(
        "Invalid ALLOWED_USER_ID. "
        "Use a numeric Telegram user ID or comma-separated IDs in .env."
    )

ALLOWED_USER_ID: int = ALLOWED_USER_IDS[0]

# LLM Provider Selection: 'openai' (default) or 'gemini'
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").strip().lower()

# OpenAI Configuration
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Gemini Configuration
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "models/text-bison-001")

# Database
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/digital_twin.db")
DB_FILE: str = DATABASE_URL.replace("sqlite:///", "")

# Vector Store
CHROMA_PATH: str = os.getenv("CHROMA_PATH", "./data/chroma")

# Transcription
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

# UI Configuration
PILLAR_EMOJI = {
    "wealth": "💰",
    "health": "❤️",
    "relationships": "🤝",
    "general": "📝",
}

PILLAR_COLORS = {
    "wealth": "W",
    "health": "H",
    "relationships": "R",
    "general": "G",
}
