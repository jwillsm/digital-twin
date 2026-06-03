"""
Query engine: retrieves relevant entries via semantic search, then
synthesizes a grounded answer using the configured LLM provider.

The provider is selected via the LLM_PROVIDER environment variable:
- 'openai' (default) — uses OpenAI's Chat API
- 'gemini' — uses Google's Generative Language API
"""

from typing import Optional

from loguru import logger

from app.provider import ProviderFactory


def query(
    user_question: str,
    pillar: Optional[str] = None,
    n_results: int = 5,
) -> str:
    """
    Run a RAG query: retrieve relevant context, then synthesize using configured provider.
    """
    try:
        provider = ProviderFactory.get_provider()
        return provider.query(user_question, pillar=pillar, n_results=n_results)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return "⚠️ Error generating response. Please try again."


def generate_daily_brief() -> str:
    """Generate a holistic daily brief across all pillars using configured provider."""
    try:
        provider = ProviderFactory.get_provider()
        return provider.brief()
    except Exception as e:
        logger.error(f"Brief error: {e}")
        return "⚠️ Error generating brief."
