# Digital Twin — Telegram MVP

A personal AI second brain with three pillars: Wealth, Health, Relationships.

## Architecture

### Three-Pillar System
The bot organizes your life into three dimensions:
- **💰 Wealth** — finances, investments, business, career decisions
- **❤️ Health** — fitness, sleep, nutrition, energy, recovery, longevity
- **🤝 Relationships** — people, social connections, emotional dynamics

### LLM Adapters
The bot supports **multiple LLM providers** via isolated adapter modules:
- **`app/openai_adapter.py`** — OpenAI's Chat API (ChatGPT)
- **`app/gemini_adapter.py`** — Google's Generative Language API (Gemini)

Each adapter exposes the same interface:
- `query_[provider](question, pillar)` — RAG-based semantic search + synthesis
- `brief_[provider](limit)` — holistic daily summary
- `run_muse_[provider]()` — autonomous pattern detection

The main `query.py` and `muse.py` modules currently delegate to **OpenAI by default**, but you can swap providers by editing those files (no changes needed to the bot logic).

## Stack
- **Bot**: python-telegram-bot
- **LLM (Primary)**: OpenAI Chat API (ChatGPT — configurable model via `OPENAI_MODEL`)
- **LLM (Alternative)**: Google Gemini (configure via `GEMINI_API_KEY` and `GEMINI_MODEL`)
- **Embeddings**: sentence-transformers (local, no API key needed)
- **Vector store**: ChromaDB (local file, no server needed)
- **Database**: SQLite (zero-setup for local dev, swap to Postgres later)
- **Transcription**: faster-whisper (local, free)
- **Tunnel**: ngrok

---

## Setup

### 1. Clone & install
```bash
cd digital-twin
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get your API keys
- **Telegram bot token**: message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`
- **OpenAI API key**: https://platform.openai.com/
- **Gemini API key** (optional): https://makersuite.google.com/app/apikey

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your keys
```
**Windows (cmd):**
```cmd
copy .env.example .env
# Then open .env in Notepad and fill in your keys
```

**Example .env** (OpenAI):
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=sk-...
ALLOWED_USER_ID=123456789
```

**Example .env** (Gemini):
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_key
ALLOWED_USER_ID=123456789
```

### 4. Run database migrations
```bash
python init_db.py
```

### 5. Start ngrok (in a separate terminal)
```bash
ngrok http 8080
# Copy the https URL, e.g. https://abc123.ngrok-free.app
```

### 6. Start the bot
```bash
python app/main.py
```

---

## Switching LLM Providers

By default, the bot uses **OpenAI**. To switch to Gemini:

### 1. Update your `.env`
```env
GEMINI_API_KEY=your_gemini_key
GEMINI_MODEL=models/text-bison-001
```

### 2. Edit `app/query.py`
Replace OpenAI imports with Gemini:
```python
from app.gemini_adapter import brief_gemini, query_gemini

def query(user_question, pillar=None, n_results=10):
    return query_gemini(user_question, pillar=pillar, n_results=n_results)

def generate_daily_brief():
    return brief_gemini()
```

### 3. Edit `app/muse.py`
Replace OpenAI imports with Gemini:
```python
from app.gemini_adapter import run_muse_gemini

def run_muse():
    return run_muse_gemini()
```

**No other changes needed** — the bot logic remains identical.

---

## Windows Setup (Detailed Guide)

### Prerequisites
- Python 3.8+ ([download](https://www.python.org/downloads/)) — **check "Add Python to PATH"** during install
- Git ([download](https://git-scm.com/download/win))
- ngrok ([download](https://ngrok.com/download)) or use `pip install pyngrok`

### Step-by-step for Windows

**1. Open Command Prompt and clone:**
```cmd
git clone https://github.com/jwillsm/digital-twin.git
cd digital-twin
```

**2. Create virtual environment:**
```cmd
python -m venv venv
venv\Scripts\activate
```
After activation, your prompt will show `(venv)` prefix.

**3. Install dependencies:**
```cmd
pip install -r requirements.txt
```

**4. Set up environment file:**
```cmd
copy .env.example .env
```
Open `.env` in Notepad and fill in:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
ALLOWED_USER_ID=your_telegram_user_id_here
```

**5. Initialize database:**
```cmd
python init_db.py
```

**6. Start ngrok (in a separate cmd window, with venv activated):**
```cmd
ngrok http 8080
```
Copy the https URL and keep the window open.

**7. Start the bot (in original cmd window):**
```cmd
python app/main.py
```

### Windows Troubleshooting
- **"python is not recognized"**: Add Python to PATH (reinstall, check "Add Python to PATH")
- **"pip: command not found"**: Use `python -m pip install -r requirements.txt`
- **"activate" fails**: Try `venv\Scripts\activate.bat` instead
- **Port 8080 in use**: Change ngrok to `ngrok http 9000`
- **ModuleNotFoundError**: Ensure `(venv)` shows in your command prompt

---

## Usage

Send any message to your Telegram bot:

| Command | What it does |
|---|---|
| Just type anything | Auto-classifies into W/H/R and saves |
| 🎤 Voice message | Transcribes → classifies → saves |
| `/query what's my financial situation?` | RAG query across all pillars |
| `/brief` | Daily summary of all three pillars |
| `/wealth` | Query only Wealth pillar |
| `/health` | Query only Health pillar |
| `/relations` | Query only Relationships pillar |
| `/stats` | Show entry counts per pillar |

---

## Data Flow

```
Telegram message
      ↓
    Triage agent (OpenAI Chat) — classifies into W/H/R + extracts entities
      ↓
  SQLite — raw storage with metadata
  ChromaDB — vector embeddings for semantic search
      ↓
    On query: RAG retrieval → LLM synthesis (OpenAI or Gemini) → Telegram reply
```

---

## Development Notes

### Adding a New Adapter
To add support for another LLM provider (e.g., Anthropic Claude, Cohere):

1. **Create `app/[provider]_adapter.py`** with these functions:
   - `query_[provider](question, pillar, n_results)` → str
   - `brief_[provider](limit)` → str
   - `run_muse_[provider]()` → list[str]

2. **Use the same agent profiles and prompts** — they're provider-agnostic

3. **Update `query.py` and `muse.py`** to delegate to your adapter

4. **Update `.env.example`** with any new config keys

5. **Test end-to-end** before committing

### Environment Variables
All configuration is environment-based (see `.env.example`):
- `TELEGRAM_BOT_TOKEN` — required
- `ALLOWED_USER_ID` — required
- `OPENAI_API_KEY`, `OPENAI_MODEL` — for OpenAI
- `GEMINI_API_KEY`, `GEMINI_MODEL` — for Gemini
- Database, Vector store, Whisper — optional, with sensible defaults
