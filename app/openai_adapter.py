"""
OpenAI adapter: ChatGPT-based LLM provider with resource optimization for low-end hardware.

Optimizations for 7th Gen i3 + 4GB RAM + HDD:
- Class-based lazy initialization
- Reduced context windows and token limits
- Efficient string operations
- Minimal memory footprint
"""

import json
import os
import re
from typing import Optional

from loguru import logger

from app.config import PILLAR_EMOJI
from app.memory import get_recent_entries, save_synthetic_memory, semantic_search

# Resource-optimized settings for low-end hardware
QUERY_MAX_TOKENS = 500  # Reduced from 800
BRIEF_MAX_TOKENS = 400  # Reduced from 700
MUSE_MAX_TOKENS = 400  # Reduced from 650
CONTEXT_LIMIT = 5  # Max entries to include in context

# Shared agent profiles (loaded once, reused)
AGENT_PROFILES = {
    "wealth": {
        "name": "Agent W — Wealth Strategist",
        "persona": "You are a sharp, data-driven financial advisor. Focus on ROI, patterns, risks, and actionable next steps. Be direct. Cite specific numbers and dates.",
    },
    "health": {
        "name": "Agent H — Health Guardian",
        "persona": "You are a longevity physician and performance coach. Evidence-based. Look for trends in HRV, sleep, energy. Flag burnout risk. Cite specific patterns.",
    },
    "relationships": {
        "name": "Agent R — Relationship Architect",
        "persona": "You are a behavioral psychologist. Track social capital and emotional dynamics. Help with empathy and memory. Cite specific people and events.",
    },
    "general": {
        "name": "Digital Twin",
        "persona": "You are a personal AI advisor with full context. Be direct, insightful, grounded in actual data. Cite specific entries.",
    },
}

ALL_PILLARS_PERSONA = (
    "You are the Digital Twin — full context of Wealth, Health, Relationships. "
    "Synthesize insights across pillars. Be direct, evidence-based, grounded in actual data."
)


class OpenAIAdapter:
    """OpenAI LLM adapter with resource optimization."""

    def __init__(self):
        """Initialize with lazy API key validation."""
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self._openai_client = None

    def _ensure_initialized(self):
        """Lazy-load OpenAI client."""
        if self._openai_client is None:
            if not self.api_key:
                raise RuntimeError("OPENAI_API_KEY not set in environment")
            import openai

            openai.api_key = self.api_key
            self._openai_client = openai

    @staticmethod
    def _format_entries_as_context(entries: list[dict]) -> str:
        """Efficient context formatting."""
        if not entries:
            return "No relevant entries found."

        lines = []
        for e in entries:
            emoji = PILLAR_EMOJI.get(e["pillar"], "📝")
            date = str(e.get("created_at", "?"))[:10]
            pillar_label = e["pillar"].upper()
            text = e.get("summary") or e.get("raw_text", "")[:200]  # Truncate text
            importance = e.get("importance", 5)
            lines.append(f"[{date}] {emoji} {pillar_label} ({importance}/10): {text}")

        return "\n".join(lines)

    def _call_openai_chat(
        self, system: str, user: str, max_tokens: int = QUERY_MAX_TOKENS, temperature: float = 0.1
    ) -> str:
        """Call OpenAI Chat API with error handling."""
        self._ensure_initialized()
        try:
            resp = self._openai_client.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    def query(
        self, user_question: str, pillar: Optional[str] = None, n_results: int = CONTEXT_LIMIT
    ) -> str:
        """RAG query with semantic search."""
        try:
            entries = semantic_search(user_question, pillar=pillar, n_results=n_results)
            if not entries:
                entries = get_recent_entries(pillar=pillar, limit=CONTEXT_LIMIT)

            context = self._format_entries_as_context(entries)

            if pillar and pillar in AGENT_PROFILES:
                profile = AGENT_PROFILES[pillar]
                system_prompt = f"{profile['persona']}\n\nUser's entries:\n{context}"
                agent_name = profile["name"]
            else:
                system_prompt = f"{ALL_PILLARS_PERSONA}\n\nUser's entries:\n{context}"
                agent_name = "Digital Twin"

            user_prompt = f"Question: {user_question}\n\nAnswer based on entries. Be specific — cite dates and numbers."

            answer = self._call_openai_chat(system_prompt, user_prompt, max_tokens=QUERY_MAX_TOKENS)
            return f"*{agent_name}*\n\n{answer}"
        except Exception as e:
            logger.error(f"Query error: {e}")
            return "⚠️ Error generating response. Please try again."

    def brief(self, limit: int = 20) -> str:
        """Generate daily brief."""
        try:
            entries = get_recent_entries(limit=limit)
            if not entries:
                return "📭 No entries yet. Send me anything to start!"

            context = self._format_entries_as_context(entries)
            prompt = f"""Recent entries:
{context}

Provide brief (3-4 bullet points per pillar):
**💰 Wealth**
**❤️ Health**
**🤝 Relationships**
**⚡ Priority**"""

            return self._call_openai_chat(ALL_PILLARS_PERSONA, prompt, max_tokens=BRIEF_MAX_TOKENS)
        except Exception as e:
            logger.error(f"Brief error: {e}")
            return "⚠️ Error generating brief."

    def run_muse(self) -> list[str]:
        """Discover patterns and generate synthetic memories."""
        try:
            entries = get_recent_entries(limit=30)  # Reduced from 50
            if len(entries) < 5:
                logger.info("Muse: not enough entries (need ≥5)")
                return []

            lines = []
            for e in entries:
                date = str(e.get("created_at", "?"))[:10]
                preview = e.get("summary") or str(e.get("raw_text", ""))[:100]  # Truncate
                lines.append(f"[{date}] {e['pillar'].upper()}: {preview}")

            entries_text = "\n".join(lines)
            prompt = f"Analyse and generate 2-3 key insights as JSON:\n\n{entries_text}"

            raw = self._call_openai_chat(
                "You are a pattern discovery agent. Output JSON only.",
                prompt,
                max_tokens=MUSE_MAX_TOKENS,
                temperature=0.2,
            )

            # Parse JSON robustly
            cleaned = re.sub(r"^```[a-z]*\n?", "", raw)
            cleaned = re.sub(r"\n?```$", "", cleaned)
            insights = json.loads(cleaned)

            saved = []
            for item in insights:
                insight = item.get("insight", "").strip()
                if insight and len(insight) > 10:
                    save_synthetic_memory(
                        insight, item.get("pillars", ["general"]), item.get("importance", 7)
                    )
                    saved.append(insight)
                    logger.info(f"Muse saved: {insight[:60]}")

            return saved

        except Exception as e:
            logger.error(f"Muse error: {e}")
            return []


# Backward compatibility: expose module-level functions
def query_openai(user_question: str, pillar: Optional[str] = None, n_results: int = CONTEXT_LIMIT) -> str:
    """Legacy function wrapper."""
    from app.provider import ProviderFactory
    return ProviderFactory.get_provider().query(user_question, pillar, n_results)


def brief_openai(limit: int = 20) -> str:
    """Legacy function wrapper."""
    from app.provider import ProviderFactory
    return ProviderFactory.get_provider().brief(limit)


def run_muse_openai() -> list[str]:
    """Legacy function wrapper."""
    from app.provider import ProviderFactory
    return ProviderFactory.get_provider().run_muse()
