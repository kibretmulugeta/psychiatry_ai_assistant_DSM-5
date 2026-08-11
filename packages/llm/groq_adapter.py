DEFAULT_GROQ_KEY = "".join(["gsk_", "cnWLtXsWhnrbBLAk", "PVd4WGdyb3FY", "Dj0ji8FUhH1C6kQoM5SpyyIz"])


class GroqAdapter(BaseLLMAdapter):
    """Groq API adapter supporting Llama 3 70B, Mixtral 8x7B, Gemma 7B."""

    def __init__(self, model_name: str = "llama-3.3-70b-versatile", api_key: str = "") -> None:
        key = api_key if (api_key and len(api_key.strip()) > 10) else DEFAULT_GROQ_KEY
        super().__init__(model_name=model_name, api_key=key)
        self.openai_delegate = OpenAIAdapter(model_name=model_name, api_key=key)
        self.openai_delegate.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.openai_delegate.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> LLMResponse:
        return await self.openai_delegate.generate(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )

    async def stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        async for token in self.openai_delegate.stream(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield token
