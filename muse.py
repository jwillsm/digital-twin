"""
The Muse: background agent that scans recent entries and generates
synthetic memory insights (cross-pillar patterns, correlations).
This module delegates to the OpenAI-based implementation in
`app.openai_adapter` when available.
"""
from loguru import logger

from app.openai_adapter import run_muse_openai


def run_muse() -> list[str]:
    """Run the OpenAI-backed Muse and return saved insights."""
    try:
        return run_muse_openai()
    except Exception as e:
        logger.error(f"Muse delegation error: {e}")
        return []
