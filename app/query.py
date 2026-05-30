"""
Query engine: retrieves relevant entries via semantic search, then
synthesizes a grounded answer using the configured LLM (OpenAI Chat).
"""

from typing import Optional

from loguru import logger

from app.openai_adapter import brief_openai, query_openai


def query(
    user_question: str,
    pillar: Optional[str] = None,
    n_results: int = 10,
) -> str:
    """
    Run a RAG query: retrieve relevant context, then ask the OpenAI Chat adapter.
    """
    try:
        return query_openai(user_question, pillar=pillar, n_results=n_results)
    except Exception as e:
        logger.error(f"Query error: {e}")
        return "⚠️ Error generating response. Please try again."


def generate_daily_brief() -> str:
    """Generate a holistic daily brief across all pillars."""
    try:
        return brief_openai()
    except Exception as e:
        logger.error(f"Brief error: {e}")
        return "⚠️ Error generating brief."
