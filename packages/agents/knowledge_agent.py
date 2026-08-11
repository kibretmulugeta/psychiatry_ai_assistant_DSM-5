"""
Knowledge Agent implementation with RAG semantic retrieval and source attributions.
"""

from typing import Any, AsyncGenerator, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.agents.base import BaseAgent
from packages.llm.base import LLMMessage
from packages.prompts.templates import build_prompt_messages
from packages.rag.embeddings.factory import EmbeddingFactory
from packages.rag.retrieval.pipeline import RetrievalPipeline, SourceAttribution


class KnowledgeResponse(BaseModel):
    """Knowledge Agent completion output with source citations."""

    content: str = Field(..., description="Assistant text response")
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    sources: List[SourceAttribution] = Field(default_factory=list, description="Retrieved source attributions")


class KnowledgeAgent(BaseAgent):
    """Knowledge Agent searching pgvector knowledge base and producing grounded answers."""

    async def process(
        self,
        input_text: str,
        history: Optional[List[LLMMessage]] = None,
        session: Optional[AsyncSession] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> KnowledgeResponse:
        """Generate response with optional RAG retrieval context and citations."""
        retrieved_context = context or ""
        sources: List[SourceAttribution] = []

        if session and not retrieved_context:
            try:
                import asyncio
                embedding_provider = EmbeddingFactory.get_provider()
                pipeline = RetrievalPipeline(session=session, embedding_provider=embedding_provider)
                ret_res = await asyncio.wait_for(pipeline.retrieve_context(query=input_text, top_k=5), timeout=2.5)
                retrieved_context = ret_res.context_text
                sources = ret_res.sources
            except Exception:
                retrieved_context = ""
                sources = []

        messages = build_prompt_messages(
            user_message=input_text,
            history=history,
            retrieved_context=retrieved_context,
        )

        llm_res = await self.llm_adapter.generate(messages=messages)
        return KnowledgeResponse(
            content=llm_res.content,
            tokens_used=llm_res.tokens_used,
            sources=sources,
        )

    async def process_stream(
        self,
        input_text: str,
        history: Optional[List[LLMMessage]] = None,
        session: Optional[AsyncSession] = None,
        context: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream completion response token-by-token."""
        retrieved_context = context or ""
        if session and not retrieved_context:
            try:
                import asyncio
                embedding_provider = EmbeddingFactory.get_provider()
                pipeline = RetrievalPipeline(session=session, embedding_provider=embedding_provider)
                ret_res = await asyncio.wait_for(pipeline.retrieve_context(query=input_text, top_k=5), timeout=2.5)
                retrieved_context = ret_res.context_text
            except Exception:
                retrieved_context = ""

        messages = build_prompt_messages(
            user_message=input_text,
            history=history,
            retrieved_context=retrieved_context,
        )

        async for token in self.llm_adapter.stream(messages=messages):
            yield token
