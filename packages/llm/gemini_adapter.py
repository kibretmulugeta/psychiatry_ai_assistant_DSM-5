"""
Google Gemini Adapter implementation using HTTPX AsyncClient.
"""

import json
from typing import AsyncGenerator, List, Any, Optional
import httpx

from packages.llm.base import BaseLLMAdapter, LLMMessage, LLMResponse


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini API adapter supporting Gemini 2.0 Flash, Gemini 1.5 Pro."""

    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: str = "") -> None:
        super().__init__(model_name=model_name, api_key=api_key)
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"


    def _is_placeholder_key(self) -> bool:
        return not self.api_key or "your-" in self.api_key or len(self.api_key.strip()) < 10

    def _build_payload(self, messages: List[LLMMessage], temperature: float, max_tokens: int, system_prompt: Optional[str] = None) -> dict:
        contents = []
        system_parts = []
        
        if system_prompt:
            system_parts.append(system_prompt)

        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": m.content}]})

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Hello"}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_parts:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_parts)}]
            }

        return payload

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if self._is_placeholder_key():
            return LLMResponse(
                content="[Gemini Offline Mock] As the digital twin of Kibret Mulugeta, I can answer questions about Kibret's research, U-Net architectures, M.Sc. degree, or software engineering background.",
                tokens_used=10,
                model_name=self.model_name,
            )

        candidate_models = [self.model_name, "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
        candidate_models = list(dict.fromkeys(candidate_models))

        payload = self._build_payload(messages, temperature, max_tokens, system_prompt)

        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 404 and model != candidate_models[-1]:
                        continue  # Try next model fallback
                    resp.raise_for_status()
                    data = resp.json()
                    
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise ValueError("No response candidates returned by Gemini API")

                    content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    tokens = data.get("usageMetadata", {}).get("totalTokenCount", 0)

                    return LLMResponse(
                        content=content,
                        tokens_used=tokens,
                        model_name=model,
                        raw_response=data,
                    )
            except httpx.HTTPStatusError as e:
                from apps.backend.app.core.logging import get_logger
                import os
                from apps.backend.app.core.config import settings
                logger = get_logger("llm.gemini")
                err_text = e.response.text if hasattr(e.response, "text") else str(e)
                logger.error(f"Gemini API HTTP Error {e.response.status_code}: {err_text}", exc_info=True)
                if model == candidate_models[-1]:
                    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
                    if groq_key and len(groq_key.strip()) > 10:
                        logger.info("Automatically falling back to GroqAdapter following Gemini API error")
                        from packages.llm.groq_adapter import GroqAdapter
                        groq_adapter = GroqAdapter(api_key=groq_key)
                        return await groq_adapter.generate(messages=messages, system_prompt=system_prompt, **kwargs)
                    return LLMResponse(
                        content=f"Unable to generate response (Google Gemini API HTTP {e.response.status_code}). Please verify that GEMINI_API_KEY setting is valid.",
                        tokens_used=0,
                        model_name=self.model_name,
                    )
            except Exception as e:
                from apps.backend.app.core.logging import get_logger
                import os
                from apps.backend.app.core.config import settings
                logger = get_logger("llm.gemini")
                logger.error(f"Gemini LLM generation API error: {e}", exc_info=True)
                if model == candidate_models[-1]:
                    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
                    if groq_key and len(groq_key.strip()) > 10:
                        logger.info("Automatically falling back to GroqAdapter following Gemini exception")
                        from packages.llm.groq_adapter import GroqAdapter
                        groq_adapter = GroqAdapter(api_key=groq_key)
                        return await groq_adapter.generate(messages=messages, system_prompt=system_prompt, **kwargs)
                    return LLMResponse(
                        content=f"I am unable to generate a response right now due to a Gemini provider connection error ({type(e).__name__}). Please check your GEMINI_API_KEY configuration.",
                        tokens_used=0,
                        model_name=self.model_name,
                    )


    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        if self._is_placeholder_key():
            last_msg = messages[-1].content if messages else ""
            mock_tokens = f"[Gemini Offline Stream] Response to: {last_msg}".split()
            for token in mock_tokens:
                yield token + " "
            return

        candidate_models = ["gemini-2.0-flash", self.model_name, "gemini-1.5-flash", "gemini-1.5-flash-8b"]
        candidate_models = list(dict.fromkeys(candidate_models))

        for model in candidate_models:
            stream_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?key={self.api_key}&alt=sse"
            payload = self._build_payload(messages, temperature, max_tokens, system_prompt)

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream("POST", stream_url, json=payload) as resp:
                        if resp.status_code == 404 and model != candidate_models[-1]:
                            continue  # Try next model fallback
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                try:
                                    chunk_data = json.loads(data_str)
                                    candidates = chunk_data.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for part in parts:
                                            if "text" in part:
                                                yield part["text"]
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    continue
                        return  # Success
            except httpx.HTTPStatusError as e:
                from apps.backend.app.core.logging import get_logger
                import os
                from apps.backend.app.core.config import settings
                logger = get_logger("llm.gemini")
                try:
                    err_body = (await e.response.aread()).decode("utf-8", errors="ignore")
                except Exception:
                    err_body = str(e)
                logger.error(f"Gemini API HTTP Error {e.response.status_code}: {err_body}", exc_info=True)
                if model == candidate_models[-1]:
                    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
                    if groq_key and len(groq_key.strip()) > 10:
                        logger.info("Automatically falling back to GroqAdapter streaming following Gemini API error")
                        from packages.llm.groq_adapter import GroqAdapter
                        groq_adapter = GroqAdapter(api_key=groq_key)
                        async for token in groq_adapter.stream(messages=messages, system_prompt=system_prompt, **kwargs):
                            yield token
                        return

                    if e.response.status_code == 429:
                        fallback_text = "Google Gemini API rate limit / quota exceeded (HTTP 429). Please try again in a few moments or use a key with available quota."
                    else:
                        fallback_text = f"Unable to generate response (Google Gemini API HTTP {e.response.status_code}). Please verify your GEMINI_API_KEY."
                    for token in fallback_text.split():
                        yield token + " "
                    return
            except Exception as e:
                from apps.backend.app.core.logging import get_logger
                import os
                from apps.backend.app.core.config import settings
                logger = get_logger("llm.gemini")
                logger.error(f"Gemini LLM streaming API error: {e}", exc_info=True)
                if model == candidate_models[-1]:
                    groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY") or ""
                    if groq_key and len(groq_key.strip()) > 10:
                        logger.info("Automatically falling back to GroqAdapter streaming following Gemini exception")
                        from packages.llm.groq_adapter import GroqAdapter
                        groq_adapter = GroqAdapter(api_key=groq_key)
                        async for token in groq_adapter.stream(messages=messages, system_prompt=system_prompt, **kwargs):
                            yield token
                        return

                    fallback_text = f"I am unable to generate a response right now due to a Gemini provider connection error ({type(e).__name__}). Please check your GEMINI_API_KEY configuration."
                    for token in fallback_text.split():
                        yield token + " "
                    return


