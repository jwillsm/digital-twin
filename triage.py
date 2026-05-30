"""
Triage agent: classifies raw text into a pillar and extracts structured metadata.
Uses Claude with a strict JSON output format.
"""
import json
import re
from typing import Optional

import anthropic
from loguru import logger

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


TRIAGE_SYSTEM = """You are the Triage Agent for a personal Digital Twin system.
Your job is to classify a personal journal entry and extract structured metadata.

Output ONLY valid JSON. No preamble, no explanation, no markdown fences.

Schema:
{
  "pillar": "wealth" | "health" | "relationships" | "general",
  "summary": "1-2 sentence distillation of the key insight or fact",
  "entities": ["list", "of", "key", "nouns"],
  "sentiment": "positive" | "neutral" | "negative",
  "importance": 1-10,
  "tags": ["optional", "topic", "tags"]
}

Pillar classification rules:
- wealth: money, investments, business, career, income, expenses, goals, revenue, deals, KPIs
- health: sleep, exercise, diet, HRV, energy, illness, recovery, mental health, habits
- relationships: people, family, friends, colleagues, conflicts, social events, feelings about others
- general: anything that doesn't clearly fit one pillar

Importance scoring:
- 9-10: major life event, significant financial decision, health crisis, relationship milestone
- 7-8: meaningful progress, pattern, or decision worth remembering
- 5-6: regular tracking, routine update
- 3-4: minor note, low signal
- 1-2: throwaway, very low value"""


def triage(text: str) -> dict:
    """
    Classify and extract metadata from raw text.
    Returns a dict with pillar, summary, entities, sentiment, importance, tags.
    Falls back gracefully on any error.
    """
    try:
        response = get_client().messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            system=TRIAGE_SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        raw = response.content[0].text.strip()

        # Strip any accidental markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

        result = json.loads(raw)
        logger.debug(f"Triage result: {result}")
        return result

    except json.JSONDecodeError as e:
        logger.warning(f"Triage JSON parse error: {e}")
    except Exception as e:
        logger.error(f"Triage error: {e}")

    # Fallback
    return {
        "pillar": "general",
        "summary": text[:200],
        "entities": [],
        "sentiment": "neutral",
        "importance": 5,
        "tags": [],
    }
