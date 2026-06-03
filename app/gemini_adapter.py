"""
Gemini adapter: provides Chat-compatible replacements for `query` and `muse`.

This mirrors the behaviour of `app/openai_adapter.py` but uses Google's
Generative Language API (Gemini) via the REST endpoint. It is intentionally
kept separate so you can switch providers without changing the rest of the bot.
"""

import os
from typing import Optional
import json
import urllib.request
import urllib.error
from loguru import logger

from app.config import PILLAR_EMOJI
from app.memory import get_recent_entries, save_synthetic_memory, semantic_search

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/text-bison-001")

QUERY_MAX_TOKENS = 800
BRIEF_MAX_TOKENS = 700
MUSE_MAX_TOKENS = 650


def _ensure_key():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in environment")


AGENT_PROFILES = {
    "wealth": {
        "name": "Agent W — Wealth Strategist",
        "persona": (
            "You are a sharp, data-driven financial advisor and operations consultant. "
            "You focus on ROI, patterns, risks, and actionable next steps. "
            "You are direct and don't sugarcoat. You cite specific numbers and dates from the entries."
        ),
    },
    "health": {
        "name": "Agent H — Health Guardian",
        "persona": (
            "You are a longevity physician and performance coach. "
            "You are evidence-based and cautious. You look for trends in HRV, sleep, energy, and habits. "
            "You act as a governor — flagging burnout risk and recovery needs. "
            "You cite specific patterns from the entries."
        ),
    },
    "relationships": {
        "name": "Agent R — Relationship Architect",
        "persona": (
            "You are a master diplomat and behavioral psychologist. "
            "You track social capital, emotional dynamics, and relationship health. "
            "You help the user lead with empathy and remember what matters to people in their life. "
            "You cite specific people and events from the entries."
        ),
    },
    "general": {
        "name": "Digital Twin",
        "persona": (
            "You are a personal AI advisor with full context of the user's life. "
            "You are direct, insightful, and grounded in the user's actual data. "
            "You cite specific entries and patterns."
        ),
    },
}


ALL_PILLARS_PERSONA = (
    "You are the user's personal Digital Twin — an AI with full context of their Wealth, Health, "
    "and Relationships. You synthesize insights across all three pillars, highlight tensions and "
    "synergies between them, and give holistic, actionable advice. You are direct, evidence-based, "
    "and always grounded in the user's actual logged data."
)


def _format_entries_as_context(entries: list[dict]) -> str:
    if not entries:
        return "No relevant entries found."

    lines = []
    for e in entries:
        emoji = PILLAR_EMOJI.get(e["pillar"], "📝")
        date = str(e.get("created_at", "?"))[:10]
        pillar_label = e["pillar"].upper()
        text = e.get("summary") or e.get("raw_text", "")
        importance = e.get("importance", 5)
        lines.append(
            f"[{date}] {emoji} {pillar_label} (importance:{importance}/10): {text}"
        )

    return "\n".join(lines)


def _call_gemini_chat(
    system: str, user: str, max_tokens: int = QUERY_MAX_TOKENS, temperature: float = 0.1
) -> str:
    _ensure_key()
    endpoint = f"https://generativelanguage.googleapis.com/v1beta2/{GEMINI_MODEL}:generate"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GEMINI_API_KEY}",
    }
    body = {
        "prompt": {"text": f"System:\n{system}\n\nUser:\n{user}"},
        "temperature": temperature,
        "maxOutputTokens": max_tokens,
    }

    req = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            # The response schema can have candidates with output.text
            if "candidates" in data and data["candidates"]:
                return data["candidates"][0].get("output", {}).get("content", "").strip()
            # Some versions return 'output'->'text'
            if "output" in data and isinstance(data["output"], dict):
                return data["output"].get("text", "").strip()
            return json.dumps(data)
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode("utf-8")
        except Exception:
            err = str(e)
        logger.error(f"Gemini API HTTP error: {err}")
        raise
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


def query_gemini(
    user_question: str, pillar: Optional[str] = None, n_results: int = 10
) -> str:
    entries = semantic_search(user_question, pillar=pillar, n_results=n_results)

    if not entries:
        entries = get_recent_entries(pillar=pillar, limit=10)

    context = _format_entries_as_context(entries)

    if pillar and pillar in AGENT_PROFILES:
        profile = AGENT_PROFILES[pillar]
        system_prompt = f"{profile['persona']}\n\nYou have access to the user's logged entries below."
        agent_name = profile["name"]
    else:
        system_prompt = f"{ALL_PILLARS_PERSONA}\n\nYou have access to the user's logged entries below."
        agent_name = "Digital Twin"

    prompt = f"""Here are the user's relevant logged entries:

<entries>
{context}
</entries>

User question: {user_question}

Answer based on the entries above. Be specific — reference actual entries, dates, and numbers.
If the entries don't contain enough information to answer confidently, say so clearly and suggest what the user should start tracking."""

    try:
        answer = _call_gemini_chat(system_prompt, prompt, max_tokens=QUERY_MAX_TOKENS)
        return f"*{agent_name}*\n\n{answer}"
    except Exception:
        return "⚠️ Error generating response. Please try again."


BRIEF_SYSTEM = ALL_PILLARS_PERSONA
BRIEF_PROMPT = """Here are the user's most recent entries across all pillars:

<entries>
{context}
</entries>

Generate a concise daily brief with this structure:

**💰 Wealth**
[2-3 key observations, any patterns or risks]

**❤️ Health**
[2-3 key observations, any patterns or risks]

**🤝 Relationships**
[2-3 key observations, any patterns or risks]

**⚡ Cross-pillar insight**
[1-2 sentences on tensions or synergies between the pillars]

**🎯 Today's priority**
[Single most important action based on current state]

Be specific, cite actual entries. Be direct — no fluff."""


def brief_gemini(limit: int = 30) -> str:
    entries = get_recent_entries(limit=limit)
    if not entries:
        return "📭 No entries yet. Send me anything to start!"

    context = _format_entries_as_context(entries)
    prompt = BRIEF_PROMPT.format(context=context)

    return _call_gemini_chat(BRIEF_SYSTEM, prompt, max_tokens=BRIEF_MAX_TOKENS)


MUSE_SYSTEM = """You are the Muse — an autonomous background intelligence agent.
Your job is to scan a person's recent life entries and discover non-obvious patterns,
correlations, and insights across their Wealth, Health, and Relationships pillars.

Output a JSON array of insight objects. No preamble, no markdown.
Schema: [{"insight": "...", "pillars": ["wealth","health"], "importance": 8}]

Generate 2-4 insights. Only output insights that have genuine signal — skip if the data is too sparse.
"""


def run_muse_gemini() -> list[str]:
    entries = get_recent_entries(limit=50)
    if len(entries) < 5:
        logger.info("Muse (Gemini): not enough entries yet (need ≥5)")
        return []

    lines = []
    for e in entries:
        date = str(e.get("created_at", "?"))[:10]
        preview = e.get("summary") or str(e.get("raw_text", ""))[:150]
        lines.append(
            f"[{date}] {e['pillar'].upper()} (importance:{e['importance']}/10): {preview}"
        )
    entries_text = "\n".join(lines)

    try:
        raw = _call_gemini_chat(
            MUSE_SYSTEM,
            f"Analyse these entries and generate synthetic memories:\n\n{entries_text}",
            max_tokens=MUSE_MAX_TOKENS,
            temperature=0.2,
        )
        import re

        cleaned = re.sub(r"^```[a-z]*\n?", "", raw)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        insights = json.loads(cleaned)

        saved = []
        for item in insights:
            insight = item.get("insight", "")
            pillars = item.get("pillars", ["general"])
            importance = item.get("importance", 7)
            if insight:
                save_synthetic_memory(insight, pillars, importance)
                saved.append(insight)
                logger.info(f"Muse (Gemini) saved insight: {insight[:80]}")

        return saved

    except Exception as e:
        logger.error(f"Muse (Gemini) error: {e}")
        return []
