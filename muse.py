"""
The Muse: background agent that scans recent entries and generates
synthetic memory insights (cross-pillar patterns, correlations).
Run periodically (e.g., daily via APScheduler or a cron job).
"""
import anthropic
from loguru import logger

from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.memory import get_recent_entries, save_synthetic_memory

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


MUSE_SYSTEM = """You are the Muse — an autonomous background intelligence agent.
Your job is to scan a person's recent life entries and discover non-obvious patterns,
correlations, and insights across their Wealth, Health, and Relationships pillars.

You generate "synthetic memories" — high-value insight notes that the user didn't
explicitly write, but that emerge from the patterns in their data.

Examples of good synthetic memories:
- "Revenue tends to drop in weeks where sleep average is below 6.5h — 3 occurrences this month"
- "You've mentioned feeling low energy on 4 occasions, always following social events"
- "Client X is mentioned positively in 5 entries; appears to be your highest-trust relationship"
- "Exercise entries correlate with higher-importance wealth entries the following day"

Output a JSON array of insight objects. No preamble, no markdown.
Schema: [{"insight": "...", "pillars": ["wealth","health"], "importance": 8}]

Generate 2-4 insights. Only output insights that have genuine signal — skip if the data is too sparse."""


def run_muse() -> list[str]:
    """
    Scan recent entries and generate synthetic memories.
    Returns list of insight strings that were saved.
    """
    entries = get_recent_entries(limit=50)
    if len(entries) < 5:
        logger.info("Muse: not enough entries yet (need ≥5)")
        return []

    # Format entries for analysis
    lines = []
    for e in entries:
        date = e["created_at"][:10] if e.get("created_at") else "?"
        lines.append(
            f"[{date}] {e['pillar'].upper()} (importance:{e['importance']}/10): "
            f"{e['summary'] or e['raw_text'][:150]}"
        )
    entries_text = "\n".join(lines)

    try:
        response = get_client().messages.create(
            model=CLAUDE_MODEL,
            max_tokens=800,
            system=MUSE_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Analyse these entries and generate synthetic memories:\n\n{entries_text}"
            }],
        )
        import json, re
        raw = response.content[0].text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        insights = json.loads(raw)

        saved = []
        for item in insights:
            insight = item.get("insight", "")
            pillars = item.get("pillars", ["general"])
            importance = item.get("importance", 7)
            if insight:
                save_synthetic_memory(insight, pillars, importance)
                saved.append(insight)
                logger.info(f"Muse saved insight: {insight[:80]}")

        return saved

    except Exception as e:
        logger.error(f"Muse error: {e}")
        return []
