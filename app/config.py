import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USER_ID: int = int(os.environ["ALLOWED_USER_ID"])

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
