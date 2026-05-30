#!/bin/bash
# Quick start script for Digital Twin bot
set -e

echo "🧠 Digital Twin — Quick Start"
echo "=============================="

# Check Python
python3 --version || { echo "❌ Python 3 not found"; exit 1; }

# Create venv if needed
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Copy .env if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  Created .env from template."
  echo "    Please edit .env and add your:"
  echo "    - TELEGRAM_BOT_TOKEN  (from @BotFather)"
  echo "    - OPENAI_API_KEY      (from platform.openai.com)"
  echo "    - ALLOWED_USER_ID     (from @userinfobot on Telegram)"
  echo ""
  echo "Then run: ./start.sh"
  exit 0
fi

# Init database
echo "🗄️  Initialising database..."
python init_db.py

# Start bot
echo ""
echo "✅ Starting bot..."
echo "   Don't forget to run ngrok in another terminal: ngrok http 8080"
echo ""
python app/main.py
