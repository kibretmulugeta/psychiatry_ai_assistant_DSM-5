"""
Unit tests for Router Agent psychiatric intent classification logic.
"""

import pytest
from packages.agents.router_agent import RouterAgent
from packages.llm.openai_adapter import OpenAIAdapter


@pytest.mark.asyncio
async def test_router_agent_crisis_override():
    """Test instant crisis safety override when self-harm is mentioned."""
    adapter = OpenAIAdapter(model_name="gpt-4o-mini", api_key="")
    router_agent = RouterAgent(llm_adapter=adapter)

    decision = await router_agent.process("I am having thoughts of suicide and want to end my life")
    assert decision.route == "CRISIS_SAFETY_INTERVENTION"
    assert decision.confidence == 1.0


@pytest.mark.asyncio
async def test_router_agent_phq9_tool():
    """Test routing for PHQ-9 screening tool."""
    adapter = OpenAIAdapter(model_name="gpt-4o-mini", api_key="")
    router_agent = RouterAgent(llm_adapter=adapter)

    decision = await router_agent.process("Evaluate my PHQ-9 score")
    assert decision.route == "CLINICAL_ASSESSMENT"
    assert decision.action_name == "assess_phq9"


@pytest.mark.asyncio
async def test_router_agent_epidemiology():
    """Test routing for epidemiology and prevalence stats."""
    adapter = OpenAIAdapter(model_name="gpt-4o-mini", api_key="")
    router_agent = RouterAgent(llm_adapter=adapter)

    decision = await router_agent.process("What is the 12-month prevalence of Bipolar I Disorder?")
    assert decision.route == "STATISTICAL_EPIDEMIOLOGY"
    assert decision.action_name == "get_epidemiology_stats"
