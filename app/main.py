"""
Digital Twin — Telegram Bot
Entry point. Run with: python app/main.py
"""

import asyncio
import os

from loguru import logger
from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import ALLOWED_USER_ID, ALLOWED_USER_IDS, PILLAR_EMOJI, TELEGRAM_BOT_TOKEN
from app.memory import get_stats, save_entry
from app.muse import run_muse
from app.query import generate_daily_brief, query
from app.transcribe import transcribe
from app.triage import triage

# ── Auth guard ────────────────────────────────────────────────────────────────


def auth(func):
    """Decorator: only respond to authorized user IDs."""

    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        user_id = getattr(update.effective_user, "id", None)
        if user_id not in ALLOWED_USER_IDS:
            details = f" Your user ID is {user_id}." if user_id else ""
            await update.message.reply_text(
                "⛔ Unauthorised." + details + "\n"
                "Update ALLOWED_USER_ID in .env with your Telegram numeric user ID. "
                "You can get it from a helper bot like @userinfobot."
            )
            return
        return await func(update, ctx)

    return wrapper


# ── Helpers ───────────────────────────────────────────────────────────────────


async def send_typing(update: Update):
    await update.message.chat.send_action(constants.ChatAction.TYPING)


async def ingest_text(text: str, source: str, update: Update):
    """Triage and save a piece of text, then confirm to user."""
    await send_typing(update)

    meta = triage(text)
    pillar = meta.get("pillar", "general")
    summary = meta.get("summary", "")
    entities = meta.get("entities", [])
    sentiment = meta.get("sentiment", "neutral")
    importance = meta.get("importance", 5)

    entry_id = save_entry(
        raw_text=text,
        pillar=pillar,
        summary=summary,
        entities=entities,
        sentiment=sentiment,
        importance=importance,
        source=source,
    )

    emoji = PILLAR_EMOJI.get(pillar, "📝")
    sentiment_emoji = {"positive": "🟢", "neutral": "🟡", "negative": "🔴"}.get(
        sentiment, "🟡"
    )

    msg = (
        f"{emoji} *{pillar.upper()}* saved (#{entry_id})\n"
        f"📊 Importance: {importance}/10  {sentiment_emoji}\n"
        f"💡 _{summary}_"
    )
    if entities:
        msg += f"\n🏷 {', '.join(entities[:5])}"

    await update.message.reply_text(msg, parse_mode="Markdown")


# ── Command handlers ──────────────────────────────────────────────────────────


@auth
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 *Digital Twin online*\n\n"
        "Just send me anything — text or voice — and I'll classify and save it.\n\n"
        "*Commands:*\n"
        "/brief — daily summary of all pillars\n"
        "/query [question] — ask anything\n"
        "/wealth [question] — query Wealth pillar\n"
        "/health [question] — query Health pillar\n"
        "/relations [question] — query Relationships pillar\n"
        "/muse — run pattern detection now\n"
        "/stats — entry counts per pillar",
        parse_mode="Markdown",
    )


@auth
async def cmd_brief(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await send_typing(update)
    brief = generate_daily_brief()
    await update.message.reply_text(brief, parse_mode="Markdown")


@auth
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = get_stats()
    if not stats:
        await update.message.reply_text("📭 No entries yet. Send me anything to start!")
        return

    lines = ["📊 *Entry counts:*"]
    total = 0
    for pillar, count in stats.items():
        emoji = PILLAR_EMOJI.get(pillar, "📝")
        lines.append(f"{emoji} {pillar.capitalize()}: {count}")
        total += count
    lines.append(f"\n*Total: {total}*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@auth
async def cmd_query(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = " ".join(ctx.args)
    if not question:
        await update.message.reply_text(
            "Usage: /query what is my current financial situation?"
        )
        return
    await send_typing(update)
    answer = query(question)
    await update.message.reply_text(answer, parse_mode="Markdown")


@auth
async def cmd_wealth(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = (
        " ".join(ctx.args)
        if ctx.args
        else "Give me a summary of my current wealth situation."
    )
    await send_typing(update)
    answer = query(question, pillar="wealth")
    await update.message.reply_text(answer, parse_mode="Markdown")


@auth
async def cmd_health(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = (
        " ".join(ctx.args)
        if ctx.args
        else "Give me a summary of my current health situation."
    )
    await send_typing(update)
    answer = query(question, pillar="health")
    await update.message.reply_text(answer, parse_mode="Markdown")


@auth
async def cmd_relations(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    question = (
        " ".join(ctx.args)
        if ctx.args
        else "Give me a summary of my current relationship landscape."
    )
    await send_typing(update)
    answer = query(question, pillar="relationships")
    await update.message.reply_text(answer, parse_mode="Markdown")


@auth
async def cmd_muse(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔮 Running Muse pattern detection...")
    await send_typing(update)
    insights = run_muse()
    if not insights:
        await update.message.reply_text(
            "🔮 *Muse*: Not enough data yet (need ≥5 entries). Keep logging!",
            parse_mode="Markdown",
        )
        return
    lines = ["🔮 *Muse found these patterns:*\n"]
    for i, insight in enumerate(insights, 1):
        lines.append(f"{i}. {insight}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Message handlers ──────────────────────────────────────────────────────────


@auth
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return
    await ingest_text(text, source="text", update=update)


@auth
async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎤 Transcribing...")

    voice = update.message.voice or update.message.audio
    if not voice:
        return

    file = await ctx.bot.get_file(voice.file_id)
    audio_bytes = await file.download_as_bytearray()

    text = transcribe(bytes(audio_bytes), file_ext="ogg")

    if not text:
        await update.message.reply_text(
            "⚠️ Couldn't transcribe audio. "
            "Make sure faster-whisper is installed: `pip install faster-whisper`"
        )
        return

    await update.message.reply_text(f"📝 *Transcript:* _{text}_", parse_mode="Markdown")
    await ingest_text(text, source="voice", update=update)


# ── Boot ──────────────────────────────────────────────────────────────────────


def main():
    logger.info("Starting Digital Twin bot...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("brief", cmd_brief))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("query", cmd_query))
    app.add_handler(CommandHandler("wealth", cmd_wealth))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(CommandHandler("relations", cmd_relations))
    app.add_handler(CommandHandler("muse", cmd_muse))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
