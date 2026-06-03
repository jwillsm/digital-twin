"""
LLM Provider factory: Dynamically select OpenAI or Gemini based on environment.

This module allows seamless switching between LLM providers without code changes.
Set LLM_PROVIDER environment variable to 'openai' or 'gemini'.
"""

import os
from typing import Optional, Protocol, runtime_checkable

from loguru import logger


@runtime_checkable
class LLMAdapter(Protocol):
    """Protocol defining the LLM adapter interface."""

    def query(
        self, user_question: str, pillar: Optional[str] = None, n_results: int = 10
    ) -> str:
        """RAG query with semantic search + synthesis."""
        ...

    def brief(self, limit: int = 30) -> str:
        """Generate a daily brief across all pillars."""
        ...

    def run_muse(self) -> list[str]:
        """Discover patterns and generate synthetic memories."""
        ...


class ProviderFactory:
    """Factory for getting the configured LLM adapter."""

    _provider: Optional[LLMAdapter] = None
    _provider_name: Optional[str] = None

    @classmethod
    def get_provider(cls) -> LLMAdapter:
        """Get the configured LLM adapter (lazy-loaded)."""
        if cls._provider is None:
            cls._load_provider()
        return cls._provider

    @classmethod
    def get_provider_name(cls) -> str:
        """Get the name of the current provider."""
        if cls._provider_name is None:
            cls._load_provider()
        return cls._provider_name

    @classmethod
    def _load_provider(cls):
        """Lazily load the appropriate provider based on environment."""
        provider_name = os.getenv("LLM_PROVIDER", "openai").lower().strip()

        if provider_name == "gemini":
            from app.gemini_adapter import GeminiAdapter

            cls._provider = GeminiAdapter()
            cls._provider_name = "Gemini"
            logger.info("LLM Provider: Gemini")

        elif provider_name == "openai":
            from app.openai_adapter import OpenAIAdapter

            cls._provider = OpenAIAdapter()
            cls._provider_name = "OpenAI"
            logger.info("LLM Provider: OpenAI")

        else:
            logger.warning(
                f"Unknown LLM_PROVIDER: {provider_name}, defaulting to OpenAI"
            )
            from app.openai_adapter import OpenAIAdapter

            cls._provider = OpenAIAdapter()
            cls._provider_name = "OpenAI"
