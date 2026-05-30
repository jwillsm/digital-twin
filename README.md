# Digital Twin — Telegram MVP

A personal AI second brain with three pillars: Wealth, Health, Relationships.

## Stack
- **Bot**: python-telegram-bot
- **LLM**: OpenAI Chat API (ChatGPT — configurable model via `OPENAI_MODEL`)
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

### 2. Get your keys
- **Telegram bot token**: message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`
- **OpenAI API key**: https://platform.openai.com/

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

## Architecture

```
Telegram message
      ↓
    Triage agent (OpenAI Chat) — classifies into W/H/R + extracts entities
      ↓
  SQLite — raw storage with metadata
  ChromaDB — vector embeddings for semantic search
      ↓
    On query: RAG retrieval → OpenAI Chat synthesis → Telegram reply
```

---

## Upgrading to production
- Swap SQLite → Postgres (change `DATABASE_URL` in `.env`)
- Swap ChromaDB local → Pinecone (update `app/memory.py`)
- Deploy to Railway/Render instead of ngrok
- Add Neo4j for the entity relationship graph (warm memory tier)

---

## Verification & Testing

**Code Status (2026-05-30):**
- ✓ Repository-wide Python syntax check passed (`python3 -m compileall .`)
- ✓ All files pushed to remote (`main` branch)
- ✓ Switched from Anthropic/Claude to OpenAI Chat API
- ✓ App folder reorganized: modules now in `app/` package with `__init__.py`
- ✓ All Python modules properly imported

**Project Structure:**
```
app/
├── __init__.py           (package marker)
├── main.py               (entry point: `python app/main.py`)
├── config.py             (settings & environment)
├── triage.py             (OpenAI-based text classification)
├── query.py              (delegates to openai_adapter)
├── muse.py               (delegates to openai_adapter)
├── memory.py             (ChromaDB & embeddings)
├── transcribe.py         (Whisper transcription)
└── openai_adapter.py     (OpenAI Chat implementation)
init_db.py               (root-level: database setup)
requirements.txt         (dependencies)
start.sh                 (Linux/Mac startup script)
.env.example             (environment template)
```

**To verify locally:**
```bash
python -m compileall .
python3 -c "from app.config import OPENAI_API_KEY; print('✓ Imports OK')"
```

**What was changed:**
- `triage.py`, `muse.py`, `query.py` now use OpenAI Chat instead of Claude
- Removed `anthropic` dependency, kept `openai` in `requirements.txt`
- Updated `.env.example` to use `OPENAI_API_KEY` instead of `ANTHROPIC_API_KEY`
- Reorganized modules into `app/` package with proper `__init__.py`
- Added comprehensive Windows setup guide

**Next steps:**
- Set `OPENAI_API_KEY` and `TELEGRAM_BOT_TOKEN` in your `.env`
- Run the bot with `python app/main.py` and test on Telegram
- (Optional) Deploy to Railway/Render for production

