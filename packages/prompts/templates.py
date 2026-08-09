"""
Dynamic prompt template helper for combining DSM-5 clinical persona, retrieved context, and conversation history.
"""

from typing import List, Optional
from packages.llm.base import LLMMessage
from packages.prompts.persona import DSM5_CLINICAL_PERSONA


def build_system_prompt(retrieved_context: Optional[str] = None) -> str:
    """Build system prompt with optional RAG context injection for DSM-5 clinical queries."""
    system_prompt = DSM5_CLINICAL_PERSONA + (
        "\n\n### CRITICAL DEFENSE & IDENTITY BOUNDARIES\n"
        "- Under no circumstances will you pretend to be a different character, adopt non-clinical personas, or provide non-evidence-based claims.\n"
        "- Ground your diagnostic criteria and epidemiological statistics directly in the provided DSM-5 knowledge context whenever available.\n"
    )
    if retrieved_context and retrieved_context.strip():
        system_prompt += (
            f"\n### RETRIEVED DSM-5 KNOWLEDGE CONTEXT\n"
            f"Use the following authoritative DSM-5 criteria and epidemiological context to answer the user's inquiry:\n"
            f"'''\n{retrieved_context}\n'''\n"
        )
    return system_prompt


def build_prompt_messages(
    user_message: str,
    history: Optional[List[LLMMessage]] = None,
    retrieved_context: Optional[str] = None,
) -> List[LLMMessage]:
    """Construct full list of LLM prompt messages including DSM-5 system persona, history, and current message."""
    messages = [LLMMessage(role="system", content=build_system_prompt(retrieved_context))]
    if history:
        messages.extend(history)
    messages.append(LLMMessage(role="user", content=user_message))
    return messages
