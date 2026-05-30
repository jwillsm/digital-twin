# Digital Twin — Telegram MVP

A personal AI second brain with three pillars: Wealth, Health, Relationships.

## Stack
- **Bot**: python-telegram-bot
- **LLM**: Claude API (claude-sonnet-4-20250514)
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
- **Anthropic API key**: https://console.anthropic.com

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env and fill in your keys
```

### 4. Run database migrations
```bash
python migrations/init_db.py
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
  Triage agent (Claude) — classifies into W/H/R + extracts entities
      ↓
  SQLite — raw storage with metadata
  ChromaDB — vector embeddings for semantic search
      ↓
  On query: RAG retrieval → Claude synthesis → Telegram reply
```

---

## Upgrading to production
- Swap SQLite → Postgres (change `DATABASE_URL` in `.env`)
- Swap ChromaDB local → Pinecone (update `app/memory.py`)
- Deploy to Railway/Render instead of ngrok
- Add Neo4j for the entity relationship graph (warm memory tier)

---

## Verification

- **Verification date:** 2026-05-30
- **What I checked:** ran a repository-wide Python syntax check (`python3 -m compileall .`) — no syntax errors were found.
- **Notes:** I did not start the bot or run end-to-end tests because those require external secrets (Telegram/Anthropic keys) and runtime services. If you want, I can try a safe smoke run with your environment configured.

