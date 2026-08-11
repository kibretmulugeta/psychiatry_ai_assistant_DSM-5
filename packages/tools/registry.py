"""
Central Tool Registry managing tool registration and execution lookup for psychiatric tools.
"""

from typing import Any, Dict, List, Optional
from packages.tools.base import BaseTool, ToolResult
from packages.tools.psychiatric_tools import (
    ClinicalSummaryReportTool,
    DSM5CodeLookupTool,
    EmergencyCrisisTool,
    EpidemiologyStatsTool,
    GAD7AssessmentTool,
    PCL5AssessmentTool,
    PHQ9AssessmentTool,
)


class ToolRegistry:
    """Registry maintaining active action tools for Psychiatric Function Calling."""

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register built-in psychiatric decision tools."""
        tools: List[BaseTool] = [
            PHQ9AssessmentTool(),
            GAD7AssessmentTool(),
            PCL5AssessmentTool(),
            DSM5CodeLookupTool(),
            EpidemiologyStatsTool(),
            ClinicalSummaryReportTool(),
            EmergencyCrisisTool(),
        ]
        for t in tools:
            self._tools[t.name] = t

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Fetch registered tool by name."""
        return self._tools.get(name)

    async def execute_tool(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute tool function by name."""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                tool_name=name,
                message=f"Requested tool '{name}' is not registered in ToolRegistry.",
            )
        return await tool.execute(**kwargs)


# Singleton instance
tool_registry = ToolRegistry()
