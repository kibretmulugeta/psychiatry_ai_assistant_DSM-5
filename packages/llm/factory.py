"""
Dynamic LLM Factory creating active provider adapter instance based on configuration settings.
"""

import os
from typing import Optional
from apps.backend.app.core.config import settings
from packages.llm.anthropic_adapter import AnthropicAdapter
from packages.llm.base import BaseLLMAdapter
from packages.llm.gemini_adapter import GeminiAdapter
from packages.llm.groq_adapter import GroqAdapter
from packages.llm.ollama_adapter import OllamaAdapter
from packages.llm.openai_adapter import OpenAIAdapter
from packages.llm.openrouter_adapter import OpenRouterAdapter


class LLMFactory:
    """Factory for instantiating LLM adapters with flexible provider auto-detection."""

    @staticmethod
    def get_adapter(provider_name: Optional[str] = None) -> BaseLLMAdapter:
        """Instantiate and return an LLM provider adapter.

        Args:
            provider_name: Optional explicit provider name ('openai', 'anthropic', 'google_gemini', etc.).
                          Defaults to settings.ACTIVE_LLM_PROVIDER.

        Returns:
            An instance of BaseLLMAdapter.
        """
        raw_provider = provider_name or settings.ACTIVE_LLM_PROVIDER
        provider = (raw_provider or "").lower().strip()

        # Check all possible Gemini API Key environment variable names
        gemini_key = (
            settings.GEMINI_API_KEY
            or getattr(settings, "GOOGLE_API_KEY", None)
            or getattr(settings, "GOOGLE_GEMINI_API_KEY", None)
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("GOOGLE_GEMINI_API_KEY")
            or ""
        )
        groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
        anthropic_key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY") or ""
        openrouter_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY") or ""
        openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY") or ""

        if provider in ["google_gemini", "gemini"] or (gemini_key and (not groq_key or "your-" in groq_key)):
            return GeminiAdapter(
                model_name="gemini-2.0-flash",
                api_key=gemini_key,
            )
        elif provider == "groq" or (groq_key and not provider):
            return GroqAdapter(
                model_name="llama-3.3-70b-versatile",
                api_key=groq_key,
            )
        elif provider == "anthropic":
            return AnthropicAdapter(
                model_name="claude-3-5-sonnet-20240620",
                api_key=anthropic_key,
            )
        elif provider == "openrouter":
            return OpenRouterAdapter(
                model_name="meta-llama/llama-3.1-70b-instruct",
                api_key=openrouter_key,
            )
        elif provider == "ollama":
            return OllamaAdapter(
                model_name="llama3:latest",
                base_url=settings.OLLAMA_BASE_URL,
            )
        elif provider == "openai":
            return OpenAIAdapter(
                model_name="gpt-4o-mini",
                api_key=openai_key,
            )
        else:
            # Fallback priority: Groq > Gemini > OpenAI
            if groq_key:
                return GroqAdapter(
                    model_name="llama-3.3-70b-versatile",
                    api_key=groq_key,
                )
            elif gemini_key:
                return GeminiAdapter(
                    model_name="gemini-2.0-flash",
                    api_key=gemini_key,
                )
            return OpenAIAdapter(
                model_name="gpt-4o-mini",
                api_key=openai_key,
            )
