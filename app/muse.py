"""
The Muse: background agent that scans recent entries and generates
synthetic memory insights (cross-pillar patterns, correlations).

The provider is selected via the LLM_PROVIDER environment variable:
- 'openai' (default) — uses OpenAI's Chat API
- 'gemini' — uses Google's Generative Language API
"""

from loguru import logger

from app.provider import ProviderFactory


def run_muse() -> list[str]:
    """Run the Muse with the configured provider and return saved insights."""
    try:
        provider = ProviderFactory.get_provider()
        return provider.run_muse()
    except Exception as e:
        logger.error(f"Muse error: {e}")
        return []
