"""Agent service for Story Pilot AI Chat Assistant.

This module provides the main agent orchestration service that handles
chat interactions, tool execution, and approval workflows.

Modes:
- Plan: AI generates a plan first, user approves, then executes
- Ask: AI asks for approval before each write action
- Auto: AI executes actions automatically
"""
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Dict, Any, List
from datetime import datetime
import json
import uuid
import re

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shinkei.models.conversation import Conversation, ConversationMessage, AgentMode
from shinkei.models.agent_persona import AgentPersona
from shinkei.agent.tools import ToolRegistry, ToolContext, NavigationContext, ToolCategory
from shinkei.agent.builtin_personas import BUILTIN_PERSONAS
from shinkei.generation.factory import ModelFactory
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


# Mode-specific system prompt additions
MODE_PROMPTS = {
    "plan": """
## Operating Mode: PLAN

Before taking any actions, you MUST first create a detailed plan and present it to the user for approval.

When the user asks you to do something that requires changes (creating beats, characters, locations, etc.):
1. First, outline your plan step-by-step
2. List each action you intend to take
3. Wait for user approval before proceeding
4. Only execute the plan after the user confirms

Format your plan like this:
```plan
## Proposed Plan

1. [Action 1 description]
2. [Action 2 description]
3. [Action 3 description]

Would you like me to proceed with this plan?
```
""",
    "ask": """
## Operating Mode: ASK

You can read and analyze data freely, but for any WRITE actions (creating or modifying beats, characters, locations, events), you MUST ask for user approval first.

When you want to make a change:
1. Describe what you want to do
2. Ask the user for permission using the structured format below
3. Wait for their approval before proceeding

Format approval requests like this:
```action
Type: [create_beat/create_character/create_location/create_event/update_beat/etc.]
Description: [What you want to do]

Parameters:
content: [The actual narrative content for beats]
beat_type: [scene/log/memory/dialogue/description]
name: [For characters/locations]
description: [Character/location description]
role: [Character's role in the story]
importance: [major/minor/background]
summary: [Brief summary if applicable]
```

IMPORTANT RULES:
1. Always include the `content` field for create_beat with the actual narrative text.
2. CREATE ONE ACTION BLOCK PER ENTITY. If you need to create multiple characters, create separate action blocks for each one. Do NOT put multiple name/description pairs in the same action block.
3. After each action is approved, propose the next one.

Example for creating multiple characters (CORRECT):
First, I'll propose adding the first character:
```action
Type: create_character
Description: Add Leo as a character

Parameters:
name: Leo
description: Systems analyst who discovered the anomaly
role: protagonist
importance: major
```

After approval, then propose the second:
```action
Type: create_character
Description: Add Maya as a character

Parameters:
name: Maya
description: Former security officer
role: supporting
importance: minor
```
""",
    "auto": """
## Operating Mode: AUTO

You have permission to execute actions automatically to help the user efficiently.
You can create beats, characters, locations, and events without asking for approval.

However:
- Always explain what you did after taking an action
- Be careful with destructive actions (deleting content)
- If unsure about the user's intent, ask for clarification first
"""
}


@dataclass
class AgentEvent:
    """Event emitted during agent chat processing."""
    type: str  # "token", "thinking", "tool_use", "tool_result", "approval_needed", "complete", "error"
    data: Dict[str, Any]

    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        return f"data: {json.dumps({'type': self.type, **self.data})}\n\n"


@dataclass
class AgentContext:
    """Context for agent execution."""
    world_id: str
    story_id: Optional[str] = None
    beat_id: Optional[str] = None
    character_id: Optional[str] = None
    location_id: Optional[str] = None


class AgentService:
    """
    Main service for Story Pilot AI Chat Assistant.

    Handles chat interactions with tool calling, approval workflows,
    and conversation management.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize agent service.

        Args:
            session: SQLAlchemy async database session
        """
        self.session = session

    async def get_or_create_conversation(
        self,
        world_id: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        title: Optional[str] = None,
        mode: str = "ask",
        persona_id: Optional[str] = None,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None
    ) -> Conversation:
        """
        Get existing conversation or create a new one.

        Args:
            world_id: World ID
            user_id: User ID
            conversation_id: Existing conversation ID (optional)
            title: Title for new conversation
            mode: Agent mode (plan, ask, auto)
            persona_id: Persona ID (optional)
            provider_override: Provider override (optional)
            model_override: Model override (optional)

        Returns:
            Conversation instance
        """
        if conversation_id:
            result = await self.session.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        # Create new conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            world_id=world_id,
            user_id=user_id,
            title=title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            mode=mode,
            persona_id=persona_id,
            provider_override=provider_override,
            model_override=model_override,
        )
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)

        logger.info(
            "conversation_created",
            conversation_id=conversation.id,
            world_id=world_id,
            user_id=user_id
        )
        return conversation

    async def _load_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Load conversation messages for LLM context."""
        result = await self.session.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at)
        )
        messages = result.scalars().all()

        formatted = []
        for msg in messages:
            formatted.append({
                "role": msg.role,
                "content": msg.content
            })
            # Include tool results if present
            if msg.tool_results:
                formatted.append({
                    "role": "tool",
                    "content": json.dumps(msg.tool_results)
                })

        return formatted

    async def _save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        reasoning: Optional[str] = None,
        tool_calls: Optional[Dict] = None,
        tool_results: Optional[Dict] = None,
        pending_approval: bool = False
    ) -> ConversationMessage:
        """Save a message to the conversation."""
        message = ConversationMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            reasoning=reasoning,
            tool_calls=tool_calls,
            tool_results=tool_results,
            pending_approval=pending_approval,
        )
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def _build_system_prompt(
        self,
        conversation: Conversation,
        context: AgentContext
    ) -> str:
        """Build system prompt including persona, world data, mode instructions, and context."""
        from shinkei.models.world import World
        from shinkei.models.character import Character
        from shinkei.models.location import Location
        from shinkei.models.story import Story

        # Get persona system prompt
        persona_prompt = ""
        if conversation.persona_id:
            result = await self.session.execute(
                select(AgentPersona).where(AgentPersona.id == conversation.persona_id)
            )
            persona = result.scalar_one_or_none()
            if persona:
                persona_prompt = persona.system_prompt

        # Load world data to include in prompt
        world_data = ""
        if context.world_id:
            world_result = await self.session.execute(
                select(World).where(World.id == context.world_id)
            )
            world = world_result.scalar_one_or_none()
            if world:
                world_data = f"""
## Current World: {world.name}

**Description:** {world.description or 'No description'}

**Tone:** {world.tone or 'Not specified'}

**Backdrop/Lore:** {world.backdrop or 'No backdrop defined'}

**World Laws:** {world.laws or {}}

**Chronology Mode:** {world.chronology_mode.value if world.chronology_mode else 'linear'}
"""
                # Load characters (limit to 10)
                chars_result = await self.session.execute(
                    select(Character).where(Character.world_id == context.world_id).limit(10)
                )
                characters = chars_result.scalars().all()
                if characters:
                    char_list = "\n".join([f"- **{c.name}**: {c.description[:100] if c.description else 'No description'}..." for c in characters])
                    world_data += f"\n**Characters ({len(characters)}):**\n{char_list}\n"

                # Load locations (limit to 10)
                locs_result = await self.session.execute(
                    select(Location).where(Location.world_id == context.world_id).limit(10)
                )
                locations = locs_result.scalars().all()
                if locations:
                    loc_list = "\n".join([f"- **{l.name}**: {l.description[:100] if l.description else 'No description'}..." for l in locations])
                    world_data += f"\n**Locations ({len(locations)}):**\n{loc_list}\n"

                # Load stories (limit to 5)
                stories_result = await self.session.execute(
                    select(Story).where(Story.world_id == context.world_id).limit(5)
                )
                stories = stories_result.scalars().all()
                if stories:
                    story_list = "\n".join([f"- **{s.title}**: {s.synopsis[:100] if s.synopsis else 'No synopsis'}..." for s in stories])
                    world_data += f"\n**Stories ({len(stories)}):**\n{story_list}\n"

        # Load current story content if a story is in context
        story_content = ""
        if context.story_id:
            from shinkei.models.story import Story
            from shinkei.models.story_beat import StoryBeat

            story_result = await self.session.execute(
                select(Story).where(Story.id == context.story_id)
            )
            story = story_result.scalar_one_or_none()

            if story:
                story_content = f"""
## Current Story: {story.title}

**Synopsis:** {story.synopsis or 'No synopsis'}
**Theme:** {story.theme or 'Not specified'}
**Status:** {story.status.value if story.status else 'draft'}
**Mode:** {story.mode.value if story.mode else 'collaborative'}
**POV:** {story.pov_type.value if story.pov_type else 'third'}

"""
                # Load story beats (limit to 10, or last 10 for long stories)
                beats_result = await self.session.execute(
                    select(StoryBeat)
                    .where(StoryBeat.story_id == context.story_id)
                    .order_by(StoryBeat.order_index)
                    .limit(15)
                )
                beats = list(beats_result.scalars().all())

                if beats:
                    story_content += "### Story Content (Beats):\n\n"
                    for beat in beats:
                        beat_content = beat.content[:500] + "..." if len(beat.content) > 500 else beat.content
                        story_content += f"**Beat {beat.order_index + 1}** ({beat.type.value if beat.type else 'scene'}):\n{beat_content}\n\n"

        # Get mode-specific instructions
        mode = conversation.mode or "ask"
        mode_instructions = MODE_PROMPTS.get(mode, MODE_PROMPTS["ask"])

        # Build available actions list
        available_actions = self._build_available_actions_prompt()

        # Default system prompt
        base_prompt = """You are Story Pilot, an AI assistant for narrative worldbuilding.
You help users manage their narrative worlds, stories, characters, and events.

Answer questions directly based on the world data provided below. Be helpful, accurate, and creative when assisting with storytelling.

{mode_instructions}

## Available Actions
You can help users with these actions:
{available_actions}

## World Data
{world_data}
{story_content}

## Current Context
- World ID: {world_id}
{story_context}
{beat_context}
"""
        story_context_line = f"- Story ID: {context.story_id}" if context.story_id else "- No story selected"
        beat_context_line = f"- Beat ID: {context.beat_id}" if context.beat_id else ""

        base = base_prompt.format(
            world_id=context.world_id,
            story_context=story_context_line,
            beat_context=beat_context_line,
            world_data=world_data,
            story_content=story_content,
            mode_instructions=mode_instructions,
            available_actions=available_actions
        )

        if persona_prompt:
            return f"{persona_prompt}\n\n{base}"
        return base

    def _build_available_actions_prompt(self) -> str:
        """Build a list of available actions for the AI."""
        actions = []

        # Read actions (no approval needed)
        read_tools = ToolRegistry.list_by_category(ToolCategory.READ)
        if read_tools:
            actions.append("**Read (no approval needed):**")
            for tool in read_tools[:5]:  # Limit to 5 for brevity
                actions.append(f"  - {tool.name}: {tool.description[:60]}...")

        # Write actions (may need approval)
        write_tools = ToolRegistry.list_by_category(ToolCategory.WRITE)
        if write_tools:
            actions.append("\n**Write (may require approval):**")
            for tool in write_tools[:5]:
                actions.append(f"  - {tool.name}: {tool.description[:60]}...")

        # Analyze actions
        analyze_tools = ToolRegistry.list_by_category(ToolCategory.ANALYZE)
        if analyze_tools:
            actions.append("\n**Analyze:**")
            for tool in analyze_tools[:3]:
                actions.append(f"  - {tool.name}: {tool.description[:60]}...")

        return "\n".join(actions) if actions else "No specific actions configured."

    def _parse_action_request(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse action request from AI response.

        Looks for ```action blocks in the response.
        Returns parsed action details or None if no action found.

        The action block format:
        ```action
        Type: create_character
        Description: What we're doing (metadata, not passed to tool)

        Parameters:
        name: Character name
        description: Character description (this IS passed to tool)
        ```
        """
        # Look for ```action blocks
        action_match = re.search(r'```action\s*(.*?)```', content, re.DOTALL)
        if not action_match:
            return None

        action_text = action_match.group(1).strip()

        # Parse the action block
        # Header section (Type, Description) goes to metadata
        # Parameters section goes to tool params
        action = {}
        tool_params = {}
        in_parameters_section = False
        current_multiline_key = None
        current_multiline_value = []

        for line in action_text.split('\n'):
            stripped = line.strip()

            # Detect Parameters: section
            if stripped.lower() == 'parameters:':
                in_parameters_section = True
                continue

            # Handle multiline content (e.g., for the content field)
            if current_multiline_key and not (': ' in stripped and not stripped.startswith((' ', '\t'))):
                # Continue collecting multiline value
                if stripped:
                    current_multiline_value.append(stripped)
                continue
            elif current_multiline_key:
                # Save the accumulated multiline value
                if in_parameters_section:
                    tool_params[current_multiline_key] = ' '.join(current_multiline_value)
                else:
                    action[current_multiline_key] = ' '.join(current_multiline_value)
                current_multiline_key = None
                current_multiline_value = []

            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Check if this might be a multiline value (content is often multiline)
                if key == 'content' and not value:
                    current_multiline_key = key
                    current_multiline_value = []
                elif value:
                    if in_parameters_section:
                        tool_params[key] = value
                    else:
                        action[key] = value

        # Don't forget the last multiline value
        if current_multiline_key and current_multiline_value:
            if in_parameters_section:
                tool_params[current_multiline_key] = ' '.join(current_multiline_value)
            else:
                action[current_multiline_key] = ' '.join(current_multiline_value)

        # Merge tool_params into action (these are the actual params)
        action.update(tool_params)

        if 'type' in action:
            return action
        return None

    def _parse_plan(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse plan from AI response.

        Looks for ```plan blocks in the response.
        Returns parsed plan details or None if no plan found.
        """
        # Look for ```plan blocks
        plan_match = re.search(r'```plan\s*(.*?)```', content, re.DOTALL)
        if not plan_match:
            return None

        plan_text = plan_match.group(1).strip()

        # Extract steps (numbered items)
        steps = []
        for line in plan_text.split('\n'):
            line = line.strip()
            # Match numbered items like "1. ", "2. ", etc.
            step_match = re.match(r'^\d+\.\s*(.+)$', line)
            if step_match:
                steps.append(step_match.group(1))

        if steps:
            return {
                "raw": plan_text,
                "steps": steps
            }
        return None

    async def chat(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        context: AgentContext
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Process a chat message and yield events.

        This is the main chat loop that handles tool execution
        and approval workflows.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            message: User message
            context: Agent context (current location)

        Yields:
            AgentEvent instances for streaming response
        """
        # Load conversation
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            yield AgentEvent(type="error", data={"message": "Conversation not found"})
            return

        # Load user to get their settings
        from shinkei.models.user import User
        user_result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()

        # Save user message
        await self._save_message(conversation_id, "user", message)

        # Build context for tools
        tool_context = ToolContext(
            session=self.session,
            user_id=user_id,
            conversation_id=conversation_id,
            navigation=NavigationContext(
                world_id=context.world_id,
                story_id=context.story_id,
                beat_id=context.beat_id,
                character_id=context.character_id,
                location_id=context.location_id,
            )
        )

        # Build system prompt
        system_prompt = await self._build_system_prompt(conversation, context)

        # Load message history
        messages = await self._load_messages(conversation_id)

        # Get LLM provider and model - use conversation override, then user settings, then default
        user_settings = user.settings if user and user.settings else {}
        user_provider = user_settings.get('llm_provider', 'openai')
        user_model = user_settings.get('llm_model')
        provider = conversation.provider_override or user_provider
        model = conversation.model_override or user_model  # Use user's model if no override

        # Get Ollama host from user settings or config
        from shinkei.config import settings as app_settings
        ollama_host = user_settings.get('llm_base_url') or app_settings.ollama_host

        # Log what we're using for debugging
        logger.info(
            "agent_llm_config",
            provider=provider,
            model=model,
            ollama_host=ollama_host if provider == "ollama" else None
        )

        try:
            # Pass host for Ollama provider
            if provider == "ollama":
                narrative_model = ModelFactory.create(provider, model_name=model, host=ollama_host)
            else:
                narrative_model = ModelFactory.create(provider, model_name=model)
        except Exception as e:
            yield AgentEvent(type="error", data={"message": f"Failed to initialize LLM: {str(e)}"})
            return

        # Get tools for LLM
        tools = ToolRegistry.to_anthropic_format() if provider == "anthropic" else ToolRegistry.to_openai_format()

        # Main chat loop
        try:
            response_content = ""
            tool_calls_made = []

            logger.info("agent_chat_starting", conversation_id=conversation_id)

            # Send thinking event immediately to keep connection alive during generation
            yield AgentEvent(type="thinking", data={"content": "Generating response..."})
            logger.info("agent_thinking_event_sent")

            # For now, do a simple non-streaming response
            # TODO: Implement streaming with tool execution loop

            # Build messages for LLM
            llm_messages = [{"role": "system", "content": system_prompt}] + messages

            # Get response from LLM
            from shinkei.generation.base import GenerationRequest

            request = GenerationRequest(
                prompt=message,
                system_prompt=system_prompt,
                model=model,
                temperature=0.7,
                max_tokens=2000
            )

            # Simple response without tool calling for initial implementation
            logger.info("agent_generating", provider=provider, model=model)
            response = await narrative_model.generate(request)
            logger.info("agent_generation_complete", content_length=len(response.content) if response.content else 0)

            response_content = response.content

            if not response_content:
                logger.warning("agent_empty_response")
                yield AgentEvent(type="error", data={"message": "Empty response from LLM"})
                return

            # Stream the response word by word (more efficient than character-by-character)
            words = response_content.split(' ')
            logger.info("agent_streaming_words", word_count=len(words))
            for i, word in enumerate(words):
                # Add space before word except for the first one
                if i > 0:
                    yield AgentEvent(type="token", data={"content": " " + word})
                else:
                    yield AgentEvent(type="token", data={"content": word})

            # Check for mode-specific patterns in response
            mode = conversation.mode or "ask"
            pending_approval = False
            parsed_action = None
            parsed_plan = None

            if mode == "plan":
                # In Plan mode, check for plan proposals
                parsed_plan = self._parse_plan(response_content)
                if parsed_plan:
                    logger.info("agent_plan_detected", steps=len(parsed_plan.get("steps", [])))
                    pending_approval = True
                    tool_calls_made = [{
                        "type": "plan",
                        "plan": parsed_plan
                    }]

            elif mode == "ask":
                # In Ask mode, check for action requests
                parsed_action = self._parse_action_request(response_content)
                if parsed_action:
                    logger.info("agent_action_detected", action_type=parsed_action.get("type"))
                    pending_approval = True
                    tool_calls_made = [{
                        "type": "action",
                        "name": parsed_action.get("type"),
                        "params": parsed_action
                    }]

            # Auto mode doesn't need approval parsing (actions are described but executed)

            logger.info("agent_saving_message", pending_approval=pending_approval)
            # Save assistant response
            assistant_message = await self._save_message(
                conversation_id,
                "assistant",
                response_content,
                tool_calls={"calls": tool_calls_made} if tool_calls_made else None,
                pending_approval=pending_approval
            )
            await self.session.commit()
            logger.info("agent_message_saved", message_id=assistant_message.id)

            # Send appropriate event based on whether approval is needed
            if pending_approval:
                if parsed_plan:
                    yield AgentEvent(
                        type="approval_needed",
                        data={
                            "message_id": assistant_message.id,
                            "tool": "plan",
                            "params": parsed_plan,
                            "message": f"Plan with {len(parsed_plan.get('steps', []))} steps proposed"
                        }
                    )
                elif parsed_action:
                    yield AgentEvent(
                        type="approval_needed",
                        data={
                            "message_id": assistant_message.id,
                            "tool": parsed_action.get("type", "unknown"),
                            "params": parsed_action,
                            "message": parsed_action.get("description", "Action proposed")
                        }
                    )

            yield AgentEvent(type="complete", data={"content": response_content, "message_id": assistant_message.id})
            logger.info("agent_complete_event_sent")

        except Exception as e:
            logger.exception("agent_chat_error", error=str(e))
            yield AgentEvent(type="error", data={"message": str(e)})

    async def approve_action(
        self,
        conversation_id: str,
        user_id: str,
        message_id: str,
        approved: bool
    ) -> AsyncGenerator[AgentEvent, None]:
        """
        Handle user approval/rejection of a pending action or plan.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            message_id: Message ID with pending action
            approved: Whether user approved the action

        Yields:
            AgentEvent instances
        """
        # Get the pending message
        result = await self.session.execute(
            select(ConversationMessage).where(
                ConversationMessage.id == message_id,
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.pending_approval == True
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            yield AgentEvent(type="error", data={"message": "No pending action found"})
            return

        if not approved:
            # User rejected - update message and notify
            message.pending_approval = False
            message.tool_results = {"status": "rejected", "reason": "User rejected action"}
            await self.session.flush()
            await self.session.commit()

            yield AgentEvent(type="complete", data={"content": "Action cancelled.", "status": "rejected"})
            return

        # User approved - check what type of approval this is
        tool_calls = message.tool_calls
        if not tool_calls or "calls" not in tool_calls:
            yield AgentEvent(type="error", data={"message": "No tool calls in message"})
            return

        # Get conversation for context
        conv_result = await self.session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        tool_context = ToolContext(
            session=self.session,
            user_id=user_id,
            conversation_id=conversation_id,
            navigation=NavigationContext(world_id=conversation.world_id if conversation else None)
        )

        results = []
        for call in tool_calls["calls"]:
            call_type = call.get("type")

            if call_type == "plan":
                # Plan approval - save confirmation message
                plan = call.get("plan", {})
                steps = plan.get("steps", [])
                results.append({
                    "type": "plan_approved",
                    "steps": steps,
                    "message": f"Plan with {len(steps)} steps approved. The AI will now proceed."
                })
                yield AgentEvent(type="tool_result", data={
                    "tool": "plan",
                    "result": {"status": "approved", "steps": steps}
                })

            elif call_type == "action":
                # Action approval - try to execute the action
                tool_name = call.get("name")
                params = call.get("params", {})

                # Map action type to actual tool
                tool_mapping = {
                    "create_beat": "create_beat",
                    "create_character": "create_character",
                    "create_location": "create_location",
                    "create_event": "create_event",
                    "update_beat": "update_beat",
                    "update_character": "update_character",
                    "update_location": "update_location",
                    "delete_beat": "delete_beat",
                }

                actual_tool = tool_mapping.get(tool_name, tool_name)

                try:
                    # Extract relevant params (exclude only 'type' metadata)
                    # Note: 'description' is kept as it's a valid param for characters/locations
                    metadata_keys = {'type'}
                    exec_params = {k: v for k, v in params.items() if k not in metadata_keys}

                    # Handle the legacy 'details' field - try to extract structured params from it
                    if 'details' in exec_params and not exec_params.get('content'):
                        details = exec_params.pop('details')
                        # Try to extract key-value pairs from details string
                        # Format: "Story ID: xyz, Content: abc, Type: plot"
                        if isinstance(details, str):
                            for part in details.split(','):
                                if ':' in part:
                                    k, v = part.split(':', 1)
                                    k = k.strip().lower().replace(' ', '_')
                                    v = v.strip().strip('"').strip("'")
                                    if k not in metadata_keys and v and k not in exec_params:
                                        exec_params[k] = v

                    logger.info(
                        "agent_action_execute",
                        tool=actual_tool,
                        params=list(exec_params.keys())
                    )

                    tool_result = await ToolRegistry.execute(actual_tool, tool_context, **exec_params)
                    results.append({"tool": actual_tool, "result": tool_result})
                    yield AgentEvent(type="tool_result", data={"tool": actual_tool, "result": tool_result})
                except ValueError as e:
                    # Tool not found or validation error
                    logger.warning("agent_action_error", tool=actual_tool, error=str(e))
                    results.append({
                        "tool": actual_tool,
                        "status": "error",
                        "message": str(e)
                    })
                    yield AgentEvent(type="tool_result", data={
                        "tool": actual_tool,
                        "result": {"status": "error", "message": str(e)}
                    })
                except Exception as e:
                    logger.exception("agent_action_exception", tool=actual_tool)
                    results.append({"tool": actual_tool, "error": str(e)})
                    yield AgentEvent(type="error", data={"tool": actual_tool, "error": str(e)})

            else:
                # Legacy format - try to execute directly
                tool_name = call.get("name")
                params = call.get("params", {})

                try:
                    tool_result = await ToolRegistry.execute(tool_name, tool_context, **params)
                    results.append({"tool": tool_name, "result": tool_result})
                    yield AgentEvent(type="tool_result", data={"tool": tool_name, "result": tool_result})
                except Exception as e:
                    results.append({"tool": tool_name, "error": str(e)})
                    yield AgentEvent(type="error", data={"tool": tool_name, "error": str(e)})

        # Update message with results
        message.pending_approval = False
        message.tool_results = {"results": results}
        await self.session.flush()
        await self.session.commit()

        yield AgentEvent(type="complete", data={"results": results, "status": "approved"})

    async def list_conversations(
        self,
        world_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Conversation], int]:
        """
        List conversations for a world.

        Args:
            world_id: World ID
            user_id: User ID
            skip: Offset
            limit: Max results

        Returns:
            Tuple of (conversations, total count)
        """
        from sqlalchemy import func

        # Count
        count_result = await self.session.execute(
            select(func.count()).where(
                Conversation.world_id == world_id,
                Conversation.user_id == user_id
            )
        )
        total = count_result.scalar_one()

        # Get conversations
        result = await self.session.execute(
            select(Conversation)
            .where(
                Conversation.world_id == world_id,
                Conversation.user_id == user_id
            )
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        conversations = list(result.scalars().all())

        return conversations, total

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        await self.session.delete(conversation)
        await self.session.flush()

        logger.info("conversation_deleted", conversation_id=conversation_id)
        return True
