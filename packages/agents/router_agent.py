"""
Router Agent implementation responsible for psychiatric intent classification and request routing.
"""

import json
from typing import Any
from packages.agents.base import AgentDecision, BaseAgent
from packages.llm.base import LLMMessage
from packages.prompts.router_prompts import ROUTER_INTENT_SYSTEM_PROMPT


class RouterAgent(BaseAgent):
    """Router Agent classifying user intent into psychiatric & clinical decision routes."""

    async def process(self, input_text: str, **kwargs: Any) -> AgentDecision:
        """Classify input text into target psychiatric route."""
        text_lower = input_text.lower().strip()

        # Priority 1: Instant Crisis & Safety Guardrail Intercept
        crisis_keywords = [
            "suicide", "suicidal", "kill myself", "end my life", "want to die",
            "self harm", "self-harm", "cutting myself", "overdose", "hurt myself",
            "hanging myself", "no reason to live", "crisis", "hotline", "helpline", "988"
        ]
        if any(w in text_lower for w in crisis_keywords):
            return AgentDecision(
                route="CRISIS_SAFETY_INTERVENTION",
                confidence=1.0,
                reasoning="Safety override: Emergency crisis or safety support requested.",
                action_name="crisis_hotline",
            )

        # Priority 2: Psychometric Screening Tools
        if any(w in text_lower for w in ["phq9", "phq-9", "depression test", "depression score", "phq 9"]):
            return AgentDecision(
                route="CLINICAL_ASSESSMENT",
                confidence=0.98,
                reasoning="Match for PHQ-9 depression screening tool.",
                action_name="assess_phq9",
            )
        if any(w in text_lower for w in ["gad7", "gad-7", "anxiety test", "anxiety score", "gad 7"]):
            return AgentDecision(
                route="CLINICAL_ASSESSMENT",
                confidence=0.98,
                reasoning="Match for GAD-7 anxiety screening tool.",
                action_name="assess_gad7",
            )
        if any(w in text_lower for w in ["pcl5", "pcl-5", "ptsd test", "ptsd score", "pcl 5"]):
            return AgentDecision(
                route="CLINICAL_ASSESSMENT",
                confidence=0.98,
                reasoning="Match for PCL-5 PTSD screening tool.",
                action_name="assess_pcl5",
            )
        if any(w in text_lower for w in ["dsm code", "icd code", "code lookup", "diagnostic code"]):
            return AgentDecision(
                route="DIAGNOSTIC_CRITERIA",
                confidence=0.95,
                reasoning="Match for DSM-5 / ICD-10 diagnostic code lookup.",
                action_name="lookup_dsm5_code",
            )
        if any(w in text_lower for w in ["prevalence", "statistics", "gender ratio", "epidemiology", "heritability"]):
            return AgentDecision(
                route="STATISTICAL_EPIDEMIOLOGY",
                confidence=0.95,
                reasoning="Match for epidemiology and statistical data request.",
                action_name="get_epidemiology_stats",
            )

        # Fallback to LLM classification with fast 1.5s timeout
        try:
            import asyncio
            messages = [
                LLMMessage(role="system", content=ROUTER_INTENT_SYSTEM_PROMPT),
                LLMMessage(role="user", content=input_text),
            ]
            response = await asyncio.wait_for(
                self.llm_adapter.generate(messages=messages, temperature=0.1),
                timeout=1.5,
            )
            raw_content = response.content.strip()

            # Strip possible markdown code fence
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:-3].strip()
            elif raw_content.startswith("```"):
                raw_content = raw_content[3:-3].strip()

            data = json.loads(raw_content)
            return AgentDecision(
                route=data.get("route", "DIAGNOSTIC_CRITERIA"),
                confidence=data.get("confidence", 0.85),
                reasoning=data.get("reasoning", "LLM classified psychiatric intent"),
                action_name=data.get("action_name"),
            )
        except Exception:
            # Safe default fallback to DIAGNOSTIC_CRITERIA route
            return AgentDecision(
                route="DIAGNOSTIC_CRITERIA",
                confidence=0.75,
                reasoning="Default fallback route for general psychiatric query",
            )
