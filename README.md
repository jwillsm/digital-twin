# Digital Twin — Telegram MVP

A personal AI second brain with three pillars: Wealth, Health, Relationships.

## Architecture

### Three-Pillar System
The bot organizes your life into three dimensions:
- **💰 Wealth** — finances, investments, business, career decisions
- **❤️ Health** — fitness, sleep, nutrition, energy, recovery, longevity
- **🤝 Relationships** — people, social connections, emotional dynamics

### LLM Provider Switching (✨ No Code Changes Needed)
The bot dynamically selects its LLM provider via the `LLM_PROVIDER` environment variable:
- **`openai`** (default) — OpenAI's Chat API (ChatGPT)
- **`gemini`** — Google's Generative Language API (Gemini)

**Just set `LLM_PROVIDER` in your `.env` file — no code edits required!**

```env
# Use OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# OR use Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
```

### Resource Optimizations (for low-end hardware)
Optimized for 7th Gen Intel i3 + 4GB RAM + HDD:
- **Lazy loading** — providers only initialized when needed
- **Reduced token limits** — lower context windows (QUERY: 500, BRIEF: 400, MUSE: 400)
- **Efficient memory management** — cached profiles, truncated entries
- **HDD-friendly** — minimal I/O operations, efficient ChromaDB queries

## Stack
- **Bot**: python-telegram-bot
- **LLM**: OpenAI Chat API or Google Gemini (configurable via env variable)
- **Embeddings**: sentence-transformers (local, no API key needed)
- **Vector store**: ChromaDB (local file, no server needed)
- **Database**: SQLite (zero-setup for local dev, swap to Postgres later)
- **Transcription**: faster-whisper (local, free)
- **Tunnel**: ngrok

---

## Quick Start

### 1. Clone & install
```bash
cd digital-twin
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get your API keys
- **Telegram bot token**: message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot`
- **OpenAI API key** (if using OpenAI): https://platform.openai.com/
- **Gemini API key** (if using Gemini): https://makersuite.google.com/app/apikey

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and choose your provider + add API keys
```

**Example .env** (OpenAI):
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
ALLOWED_USER_ID=123456789
```

**Example .env** (Gemini):
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_key
ALLOWED_USER_ID=123456789
```

### 4. Initialize database
```bash
python init_db.py
```

### 5. Start ngrok (in a separate terminal)
```bash
ngrok http 8080
```

### 6. Start the bot
```bash
python app/main.py
```

---

## Windows Setup (Detailed)

### Prerequisites
- Python 3.8+ ([download](https://www.python.org/downloads/)) — **check "Add Python to PATH"**
- Git ([download](https://git-scm.com/download/win))
- ngrok ([download](https://ngrok.com/download)) or `pip install pyngrok`

### Step-by-step

**1. Clone:**
```cmd
git clone https://github.com/jwillsm/digital-twin.git
cd digital-twin
```

**2. Create virtual environment:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies:**
```cmd
pip install -r requirements.txt
```

**4. Configure environment:**
```cmd
copy .env.example .env
```
Open `.env` in Notepad and fill in your tokens and API keys.

**5. Initialize database:**
```cmd
python init_db.py
```

**6. Start ngrok (separate terminal):**
```cmd
ngrok http 8080
```

**7. Start the bot:**
```cmd
python app/main.py
```

### Troubleshooting
- **"python is not recognized"**: Add Python to PATH (reinstall with "Add Python to PATH")
- **"pip: command not found"**: Use `python -m pip install -r requirements.txt`
- **"activate" fails**: Try `venv\Scripts\activate.bat`
- **ModuleNotFoundError**: Ensure `(venv)` shows in your prompt

---

## Usage

Send any message to your bot:

| Command | What it does |
|---|---|
| Any text | Auto-classifies into W/H/R and saves |
| 🎤 Voice | Transcribes → classifies → saves |
| `/query [question]` | RAG query across all pillars |
| `/brief` | Daily summary of all pillars |
| `/wealth [question]` | Query Wealth pillar only |
| `/health [question]` | Query Health pillar only |
| `/relations [question]` | Query Relationships pillar only |
| `/stats` | Show entry counts |

---

## Architecture Details

### Data Flow
```
User message (text or voice)
      ↓
[Transcription if voice → Triage to W/H/R]
      ↓
[SQLite] store raw entry
[ChromaDB] compute embedding
      ↓
On query: Semantic search → Retrieve context → LLM synthesis → Reply
```

### Provider Factory Pattern
The `app/provider.py` module dynamically loads the correct adapter at runtime:

```python
from app.provider import ProviderFactory

# Automatically uses the provider from LLM_PROVIDER env var
provider = ProviderFactory.get_provider()
answer = provider.query(question)
```

**No code changes needed to switch providers!**

---

## Development

### Adding a New LLM Provider

1. **Create `app/[provider]_adapter.py`** with a class:
```python
class MyProviderAdapter:
    def query(self, user_question, pillar=None, n_results=5) -> str: ...
    def brief(self, limit=20) -> str: ...
    def run_muse(self) -> list[str]: ...
```

2. **Update `app/provider.py`** to recognize your provider:
```python
elif provider_name == "myprovider":
    from app.myprovider_adapter import MyProviderAdapter
    cls._provider = MyProviderAdapter()
```

3. **Update `.env.example`** with new config keys

4. **Test end-to-end**

### Performance Notes (Low-End Hardware)
- Token limits are reduced to minimize API latency and memory usage
- Context is limited to 5 most relevant entries (tunable in adapters)
- Lazy loading defers initialization until first use
- ChromaDB uses cosine distance (efficient on HDDs)
- Batch embeddings when possible

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `LLM_PROVIDER` | `openai` | Choose adapter: `openai` or `gemini` |
| `OPENAI_API_KEY` | — | OpenAI authentication |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model |
| `GEMINI_API_KEY` | — | Gemini authentication |
| `GEMINI_MODEL` | `models/text-bison-001` | Gemini model |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot auth |
| `ALLOWED_USER_ID` | — | Your Telegram user ID |
| `DATABASE_URL` | `sqlite:///./data/digital_twin.db` | SQLite path |
| `CHROMA_PATH` | `./data/chroma` | ChromaDB vector store |
| `WHISPER_MODEL` | `base` | Transcription model |

---

## License

MIT — Use freely, modify, share.
