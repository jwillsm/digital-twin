"""
Query engine: retrieves relevant entries via semantic search, then
synthesizes a grounded answer using the configured LLM (OpenAI Chat).
"""
from typing import Optional

from loguru import logger

from app.config import PILLAR_EMOJI
from app.memory import semantic_search, get_recent_entries
from app.openai_adapter import query_openai


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
        date = e["created_at"][:10] if e.get("created_at") else "?"
        pillar_label = e["pillar"].upper()
        text = e["summary"] or e["raw_text"]
        importance = e.get("importance", 5)
        lines.append(f"[{date}] {emoji} {pillar_label} (importance:{importance}/10): {text}")

    return "\n".join(lines)


def query(
    user_question: str,
    pillar: Optional[str] = None,
    n_results: int = 10,
) -> str:
    """
    Run a RAG query: retrieve relevant context, then ask Claude to synthesize.
    If pillar is None, searches all pillars and uses the holistic persona.
    """
    entries = semantic_search(user_question, pillar=pillar, n_results=n_results)

    if not entries:
        # Fall back to recent entries if no semantic results
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
        answer = query_openai(prompt, pillar=pillar, n_results=n_results)
        return answer
    except Exception as e:
        """
        Query engine: retrieves relevant entries via semantic search, then
        synthesizes a grounded answer using the configured LLM (OpenAI Chat).
        """
def generate_daily_brief() -> str:
    """Generate a holistic daily brief across all three pillars."""
    all_entries = get_recent_entries(limit=30)

    if not all_entries:
        return "📭 No entries yet. Start logging by sending me anything about your wealth, health, or relationships!"

    context = _format_entries_as_context(all_entries)

    prompt = f"""Here are the user's most recent entries across all pillars:

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

    try:
        return query_openai(prompt, pillar=None, n_results=20)
    except Exception as e:
        logger.error(f"Brief error: {e}")
        return "⚠️ Error generating brief."
