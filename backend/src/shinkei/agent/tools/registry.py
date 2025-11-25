"""Tool registry for Story Pilot agent.

This module provides the core tool registry system that manages all tools
available to the AI agent, including their definitions, handlers, and
provider-specific formatting.
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, List, Any, TYPE_CHECKING
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from shinkei.agent.tools.context import ToolContext


class ToolCategory(str, Enum):
    """Categories for organizing tools."""
    READ = "read"           # Tools that only read data
    WRITE = "write"         # Tools that modify data
    ANALYZE = "analyze"     # Tools that analyze content
    NAVIGATE = "navigate"   # Tools that affect UI navigation
    GRAPH = "graph"         # Tools for GraphRAG operations


@dataclass
class ToolDefinition:
    """
    Definition of a tool available to the agent.

    Attributes:
        name: Unique tool identifier
        description: Human-readable description for the AI
        parameters: JSON Schema for tool parameters
        handler: Async function to execute the tool
        requires_approval: Whether tool requires user approval in Ask mode
        category: Tool category for organization
        enabled: Whether tool is currently enabled
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    requires_approval: bool = False
    category: ToolCategory = ToolCategory.READ
    enabled: bool = True

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool use format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }


class ToolRegistry:
    """
    Registry for managing agent tools.

    This is a singleton-style registry that holds all available tools
    and provides methods for retrieving them in various formats.
    """
    _tools: Dict[str, ToolDefinition] = {}

    @classmethod
    def register(cls, tool: ToolDefinition) -> None:
        """
        Register a tool with the registry.

        Args:
            tool: Tool definition to register
        """
        cls._tools[tool.name] = tool

    @classmethod
    def unregister(cls, name: str) -> bool:
        """
        Unregister a tool from the registry.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was removed, False if not found
        """
        if name in cls._tools:
            del cls._tools[name]
            return True
        return False

    @classmethod
    def get(cls, name: str) -> Optional[ToolDefinition]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            Tool definition or None if not found
        """
        return cls._tools.get(name)

    @classmethod
    def list_all(cls) -> List[ToolDefinition]:
        """Get all registered tools."""
        return list(cls._tools.values())

    @classmethod
    def list_enabled(cls) -> List[ToolDefinition]:
        """Get all enabled tools."""
        return [t for t in cls._tools.values() if t.enabled]

    @classmethod
    def list_by_category(cls, category: ToolCategory) -> List[ToolDefinition]:
        """
        Get tools by category.

        Args:
            category: Tool category to filter by

        Returns:
            List of tools in that category
        """
        return [t for t in cls._tools.values() if t.category == category and t.enabled]

    @classmethod
    def list_requiring_approval(cls) -> List[ToolDefinition]:
        """Get all tools that require approval in Ask mode."""
        return [t for t in cls._tools.values() if t.requires_approval and t.enabled]

    @classmethod
    def to_openai_format(cls, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all tools in OpenAI function calling format.

        Args:
            enabled_only: Only include enabled tools

        Returns:
            List of tool definitions in OpenAI format
        """
        tools = cls.list_enabled() if enabled_only else cls.list_all()
        return [t.to_openai_format() for t in tools]

    @classmethod
    def to_anthropic_format(cls, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all tools in Anthropic tool use format.

        Args:
            enabled_only: Only include enabled tools

        Returns:
            List of tool definitions in Anthropic format
        """
        tools = cls.list_enabled() if enabled_only else cls.list_all()
        return [t.to_anthropic_format() for t in tools]

    @classmethod
    async def execute(
        cls,
        tool_name: str,
        context: "ToolContext",
        **params
    ) -> Dict[str, Any]:
        """
        Execute a tool by name.

        Args:
            tool_name: Tool name to execute
            context: Execution context
            **params: Tool parameters

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
        """
        tool = cls.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        if not tool.enabled:
            raise ValueError(f"Tool is disabled: {tool_name}")

        return await tool.handler(context, **params)

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (useful for testing)."""
        cls._tools.clear()


def tool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    requires_approval: bool = False,
    category: ToolCategory = ToolCategory.READ
):
    """
    Decorator to register a function as a tool.

    Usage:
        @tool(
            name="get_character",
            description="Get character details",
            parameters={
                "type": "object",
                "properties": {
                    "character_id": {"type": "string"}
                },
                "required": ["character_id"]
            }
        )
        async def get_character(context: ToolContext, character_id: str) -> dict:
            ...

    Args:
        name: Tool name
        description: Tool description
        parameters: JSON Schema for parameters
        requires_approval: Whether tool needs user approval
        category: Tool category
    """
    def decorator(func: Callable) -> Callable:
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
            requires_approval=requires_approval,
            category=category
        )
        ToolRegistry.register(tool_def)
        return func
    return decorator
