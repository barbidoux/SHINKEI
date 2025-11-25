"""Story Pilot AI Chat Assistant agent module."""
from shinkei.agent.agent_service import AgentService, AgentEvent, AgentContext
from shinkei.agent.tools import (
    ToolRegistry,
    ToolDefinition,
    ToolCategory,
    tool,
    ToolContext,
    NavigationContext,
)
from shinkei.agent.builtin_personas import BUILTIN_PERSONAS

# Import tools to trigger registration via decorators
from shinkei.agent.tools import read_tools  # noqa: F401
from shinkei.agent.tools import write_tools  # noqa: F401
from shinkei.agent.tools import analyze_tools  # noqa: F401
from shinkei.agent.tools import graph_tools  # noqa: F401

# Import services
from shinkei.agent.graph_rag_service import GraphRAGService

__all__ = [
    "AgentService",
    "AgentEvent",
    "AgentContext",
    "ToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    "tool",
    "ToolContext",
    "NavigationContext",
    "BUILTIN_PERSONAS",
    "GraphRAGService",
]
