"""
Unit tests for psychiatric function calling tools and Central ToolRegistry.
"""

import pytest
from packages.tools.registry import tool_registry


@pytest.mark.asyncio
async def test_assess_phq9_tool():
    """Test PHQ-9 depression scale evaluation tool."""
    res = await tool_registry.execute_tool("assess_phq9", total_score=12)
    assert res.success is True
    assert res.tool_name == "assess_phq9"
    assert res.data["score"] == 12
    assert res.data["severity_level"] == "Moderate Depression"


@pytest.mark.asyncio
async def test_assess_gad7_tool():
    """Test GAD-7 anxiety scale evaluation tool."""
    res = await tool_registry.execute_tool("assess_gad7", total_score=16)
    assert res.success is True
    assert res.tool_name == "assess_gad7"
    assert res.data["score"] == 16
    assert res.data["severity_level"] == "Severe Anxiety"


@pytest.mark.asyncio
async def test_assess_pcl5_tool():
    """Test PCL-5 PTSD checklist tool."""
    res = await tool_registry.execute_tool("assess_pcl5", total_score=40)
    assert res.success is True
    assert res.tool_name == "assess_pcl5"
    assert res.data["threshold_met"] is True


@pytest.mark.asyncio
async def test_lookup_dsm5_code_tool():
    """Test DSM-5 ICD-10 diagnostic code lookup tool."""
    res = await tool_registry.execute_tool("lookup_dsm5_code", query="Depressive")
    assert res.success is True
    assert len(res.data["results"]) >= 1


@pytest.mark.asyncio
async def test_get_epidemiology_stats_tool():
    """Test epidemiology statistics retrieval tool."""
    res = await tool_registry.execute_tool("get_epidemiology_stats", disorder_name="Schizophrenia")
    assert res.success is True
    assert res.data["name"] == "Schizophrenia"
    assert "12m_prevalence" in res.data


@pytest.mark.asyncio
async def test_invalid_tool():
    """Test execution of non-existent tool."""
    res = await tool_registry.execute_tool("non_existent_tool")
    assert res.success is False
