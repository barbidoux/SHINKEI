"""Ollama provider implementation."""
from typing import AsyncGenerator, Optional, List, Dict, Any
import json
from ollama import AsyncClient
from shinkei.generation.base import (
    NarrativeModel,
    GenerationRequest,
    GenerationResponse,
    GenerationContext,
    GenerationConfig,
    GeneratedBeat,
    ModificationContext,
    ModifiedBeat,
    EntitySuggestion,
    EntityExtractionContext,
    CharacterGenerationContext,
    LocationGenerationContext,
    CoherenceValidationContext,
    CoherenceValidationResult,
    EventGenerationContext,
    EventExtractionContext,
    EventCoherenceContext,
    EventSuggestion,
    TemplateGenerationContext,
    OutlineGenerationContext,
    GeneratedTemplate,
    StoryOutline
)
from shinkei.generation.beat_prompts import BeatGenerationPrompts
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class OllamaModel(NarrativeModel):
    """Ollama implementation of NarrativeModel."""

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Ollama client.

        Args:
            host: Ollama host URL (optional)
            model: Default model name (optional, defaults to llama3)
        """
        self.client = AsyncClient(host=host)
        self.model = model or "llama3"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using Ollama.
        """
        model = request.model or self.model

        # Ollama supports system prompt in options or as a message
        # Add explicit instruction to respond with text, not function calls
        system_content = request.system_prompt or ""
        system_content += "\n\nIMPORTANT: Respond with plain text only. Do not use function calls or tool calls."

        messages = []
        messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": request.prompt})

        options = {
            "temperature": request.temperature,
        }
        if request.stop_sequences:
            options["stop"] = request.stop_sequences
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        logger.debug("ollama_generate_request", model=model, messages_count=len(messages))

        response = await self.client.chat(
            model=model,
            messages=messages,
            options=options,
        )

        # Log full response structure for debugging
        logger.debug("ollama_response_keys", keys=list(response.keys()) if isinstance(response, dict) else "not_dict")

        content = response.get('message', {}).get('content', '')

        # Handle case where model returns tool calls instead of content
        if not content:
            tool_calls = response.get('message', {}).get('tool_calls', [])
            if tool_calls:
                logger.warning("ollama_returned_tool_calls", tool_calls=tool_calls)
                # Convert tool calls to a text response explaining the issue
                content = f"I tried to use a tool ({tool_calls[0].get('function', {}).get('name', 'unknown')}), but I'll respond directly instead:\n\nI'm Story Pilot, your AI assistant for narrative worldbuilding. How can I help you with your world today?"
            else:
                logger.warning("ollama_empty_content_no_tools", response_message=response.get('message', {}))
                content = "I'm here to help with your narrative world. What would you like to know or create?"

        finish_reason = response.get('done_reason', 'stop')

        # Ollama usage stats might vary
        usage = {
            "prompt_eval_count": response.get('prompt_eval_count', 0),
            "eval_count": response.get('eval_count', 0),
        }

        return GenerationResponse(
            content=content,
            model_used=response.get('model', model),
            usage=usage,
            finish_reason=finish_reason,
        )

    async def stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """
        Stream generated text using Ollama.
        """
        model = request.model or self.model
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        options = {
            "temperature": request.temperature,
        }
        if request.stop_sequences:
            options["stop"] = request.stop_sequences
        if request.max_tokens:
            options["num_predict"] = request.max_tokens

        stream = self.client.chat(
            model=model,
            messages=messages,
            options=options,
            stream=True,
        )

        async for chunk in stream:
            content = chunk['message']['content']
            if content:
                yield content

    # Narrative-specific methods

    async def generate_next_beat(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> GeneratedBeat:
        """
        Generate next narrative beat using Ollama.

        Args:
            context: Full narrative context (World + Story + Beats)
            config: Generation parameters

        Returns:
            GeneratedBeat with text, summary, time label, and metadata
        """
        # Build narrative-aware prompts
        system_prompt = BeatGenerationPrompts.build_system_prompt(context)
        user_prompt = BeatGenerationPrompts.build_user_prompt(context)

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Configure options
        options = {
            "temperature": config.temperature,
            "num_predict": config.max_tokens,
        }
        if config.stop_sequences:
            options["stop"] = config.stop_sequences

        # Use model from config, fallback to instance default
        model = config.model or self.model

        logger.info(
            "generating_beat_with_ollama",
            story_title=context.story_title,
            world_name=context.world_name,
            model=model
        )

        try:
            # Step 1: Generate AI reasoning/thoughts
            reasoning_prompt = (
                "Before generating the next beat, think step-by-step about:\n"
                "1. How should the narrative continue given the world's tone and recent events?\n"
                "2. What narrative tension or development is needed?\n"
                "3. How can this beat advance the story while maintaining coherence?\n"
                "4. What specific elements from the world laws and backdrop should influence this beat?\n\n"
                "Provide your reasoning in 2-4 sentences."
            )

            reasoning_messages = messages + [{"role": "user", "content": reasoning_prompt}]

            reasoning_response = await self.client.chat(
                model=model,
                messages=reasoning_messages,
                options={"temperature": 0.5, "num_predict": 300}
            )

            reasoning = reasoning_response['message']['content']

            # Step 2: Generate narrative text using reasoning as context
            generation_messages = messages + [
                {"role": "assistant", "content": reasoning},
                {"role": "user", "content": "Now, write the narrative beat based on your reasoning above."}
            ]

            response = await self.client.chat(
                model=model,
                messages=generation_messages,
                options=options,
            )

            generated_text = response['message']['content']

            # HIGH PRIORITY FIX 2.6 & 2.7: Generate summary and determine beat type in parallel
            # with error handling for each task
            summary_task = self.summarize(generated_text)
            beat_type_task = self.determine_beat_type(generated_text, context)

            # Await both tasks with individual error handling
            try:
                summary = await summary_task
            except Exception as e:
                logger.error("summary_task_failed", error=str(e))
                summary = "Summary generation failed."

            try:
                beat_type = await beat_type_task
            except Exception as e:
                logger.error("beat_type_task_failed", error=str(e))
                beat_type = "scene"

            # Determine time label
            local_time_label = BeatGenerationPrompts.build_time_label_prompt(context)

            # Extract world event ID if present
            world_event_id = None
            if context.target_world_event:
                world_event_id = context.target_world_event.get('id')

            # Create metadata
            metadata = {
                "model": response.get('model', model),
                "prompt_eval_count": response.get('prompt_eval_count', 0),
                "eval_count": response.get('eval_count', 0),
                "finish_reason": response.get('done_reason', 'stop')
            }

            logger.info(
                "beat_generated_successfully",
                story_title=context.story_title,
                beat_type=beat_type,
                eval_count=metadata["eval_count"]
            )

            return GeneratedBeat(
                text=generated_text,
                summary=summary,
                local_time_label=local_time_label,
                reasoning=reasoning,
                world_event_id=world_event_id,
                beat_type=beat_type,
                metadata=metadata
            )

        except Exception as e:
            logger.error("ollama_beat_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate beat with Ollama: {str(e)}")

    async def summarize(self, text: str) -> str:
        """
        Generate summary using Ollama.

        Args:
            text: Narrative text to summarize

        Returns:
            2-3 sentence summary
        """
        prompt = BeatGenerationPrompts.build_summary_prompt(text)

        messages = [
            {
                "role": "system",
                "content": "You are a concise summarizer. Create brief 2-3 sentence summaries."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        options = {
            "temperature": 0.3,  # Lower temperature for consistency
            "num_predict": 150  # Short summary
        }

        try:
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
            )

            summary = response['message']['content'].strip()
            return summary

        except Exception as e:
            logger.error("ollama_summarization_error", error=str(e))
            return "Summary generation failed."

    async def determine_beat_type(self, text: str, context: GenerationContext) -> str:
        """
        HIGH PRIORITY FIX 2.6: Determine appropriate beat type using AI.

        Previously Ollama hardcoded beat_type="scene". This method provides
        consistent behavior with OpenAI and Anthropic providers.

        Args:
            text: Narrative text to classify
            context: Generation context for additional hints

        Returns:
            Beat type: "scene", "summary", or "note"
        """
        prompt = f"""Classify this narrative beat into ONE of these types:
- "scene": Detailed, immersive narrative with dialogue, action, and sensory details
- "summary": Condensed recap of events or time passage
- "note": Brief observation, thought, or transitional text

TEXT:
{text[:500]}...

Respond with ONLY one word: scene, summary, or note."""

        messages = [
            {
                "role": "system",
                "content": "You are a narrative classification assistant. Analyze text and identify its narrative type. Respond with only one word."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        options = {
            "temperature": 0.2,  # Very low temperature for consistent classification
            "num_predict": 10
        }

        try:
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                options=options,
            )

            beat_type = (response['message']['content'] or "scene").strip().lower()

            # Validate response is one of the valid types
            if beat_type not in ["scene", "summary", "note"]:
                logger.warning(
                    "invalid_beat_type_defaulting_to_scene",
                    received=beat_type
                )
                return "scene"

            return beat_type

        except Exception as e:
            logger.error("ollama_beat_type_determination_error", error=str(e))
            return "scene"  # Default fallback

    async def modify_beat(
        self,
        context: ModificationContext,
        config: GenerationConfig
    ) -> ModifiedBeat:
        """
        Modify an existing story beat based on user instructions.

        Args:
            context: Modification context with original beat and instructions
            config: Generation parameters

        Returns:
            ModifiedBeat with modified content, summary, and reasoning
        """
        model = config.model or self.model

        logger.info(
            "modifying_beat_with_ollama",
            story_title=context.story_title,
            world_name=context.world_name,
            model=model,
            scope=context.scope
        )

        try:
            # Build system prompt with world/story context
            system_prompt = (
                f"You are modifying a narrative beat from the story '{context.story_title}' "
                f"set in the world '{context.world_name}'.\n\n"
                f"World Tone: {context.world_tone}\n"
                f"World Backdrop: {context.world_backdrop}\n"
                f"World Laws: {context.world_laws}\n\n"
                f"Story Synopsis: {context.story_synopsis}\n"
                f"POV Type: {context.story_pov_type}\n\n"
                "Your task is to modify the existing narrative beat according to user instructions "
                "while maintaining narrative coherence, world rules, and the established tone."
            )

            # Step 1: Generate reasoning for modifications
            reasoning_prompt = (
                f"ORIGINAL BEAT:\n{context.original_content}\n\n"
                f"MODIFICATION INSTRUCTIONS:\n{context.modification_instructions}\n\n"
                "Before making changes, think step-by-step about:\n"
                "1. What specific changes does the user want?\n"
                "2. How can these changes be made while maintaining narrative coherence?\n"
                "3. What impact will these modifications have on the story flow?\n"
                "4. How can the world's tone and laws be preserved in the modifications?\n\n"
                "Provide your reasoning in 2-4 sentences."
            )

            reasoning_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reasoning_prompt}
            ]

            reasoning_response = await self.client.chat(
                model=model,
                messages=reasoning_messages,
                options={"temperature": 0.5, "num_predict": 300}
            )

            reasoning = reasoning_response['message']['content']

            # Step 2: Generate modified content
            modification_prompt = (
                f"ORIGINAL BEAT:\n{context.original_content}\n\n"
                f"MODIFICATION INSTRUCTIONS:\n{context.modification_instructions}\n\n"
                f"YOUR REASONING:\n{reasoning}\n\n"
                "Now, rewrite the beat according to the instructions and your reasoning. "
                "Provide ONLY the modified narrative text, without any preamble or explanation."
            )

            modification_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": modification_prompt}
            ]

            options = {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
            }

            response = await self.client.chat(
                model=model,
                messages=modification_messages,
                options=options,
            )

            modified_content = response['message']['content']

            # Step 3: Generate new summary if in scope
            modified_summary = context.original_summary
            if "summary" in context.scope:
                modified_summary = await self.summarize(modified_content)

            # Step 4: Update time label if in scope
            modified_time_label = context.original_time_label
            if "time_label" in context.scope and modified_time_label:
                # Check if time label needs updating based on content changes
                time_check_prompt = (
                    f"Original time label: {context.original_time_label}\n"
                    f"Original content: {context.original_content[:200]}...\n"
                    f"Modified content: {modified_content[:200]}...\n\n"
                    "Does the time label need to be updated based on the content changes? "
                    "If yes, provide ONLY the new time label. If no, respond with 'NO_CHANGE'."
                )

                time_response = await self.client.chat(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a narrative timeline assistant."},
                        {"role": "user", "content": time_check_prompt}
                    ],
                    options={"temperature": 0.3, "num_predict": 50}
                )

                time_result = time_response['message']['content'].strip()
                if time_result != "NO_CHANGE":
                    modified_time_label = time_result

            # Step 5: World event link (preserve or None if in scope)
            modified_world_event_id = context.original_world_event_id
            if "world_event" in context.scope:
                # For now, preserve the original. In future, could add logic to
                # suggest different world events based on modifications
                pass

            # Create metadata
            metadata = {
                "model": response.get('model', model),
                "prompt_eval_count": response.get('prompt_eval_count', 0),
                "eval_count": response.get('eval_count', 0),
                "finish_reason": response.get('done_reason', 'stop')
            }

            logger.info(
                "beat_modified_successfully",
                story_title=context.story_title,
                eval_count=metadata["eval_count"]
            )

            return ModifiedBeat(
                modified_content=modified_content,
                modified_summary=modified_summary,
                modified_time_label=modified_time_label,
                modified_world_event_id=modified_world_event_id,
                reasoning=reasoning,
                metadata=metadata
            )

        except Exception as e:
            logger.error("ollama_beat_modification_error", error=str(e))
            raise RuntimeError(f"Failed to modify beat with Ollama: {str(e)}")

    async def generate_next_beat_stream(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> AsyncGenerator[str, None]:
        """
        Stream the next narrative beat content progressively.

        Args:
            context: Full narrative context (World + Story + Beats)
            config: Generation parameters

        Yields:
            Content chunks as they're generated
        """
        # Build narrative-aware prompts
        system_prompt = BeatGenerationPrompts.build_system_prompt(context)
        user_prompt = BeatGenerationPrompts.build_user_prompt(context)

        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Configure options
        options = {
            "temperature": config.temperature,
            "num_predict": config.max_tokens,
        }
        if config.stop_sequences:
            options["stop"] = config.stop_sequences

        # Use model from config, fallback to instance default
        model = config.model or self.model

        logger.info(
            "streaming_beat_with_ollama",
            story_title=context.story_title,
            world_name=context.world_name,
            model=model
        )

        try:
            # Step 1: Generate AI reasoning/thoughts (non-streaming)
            reasoning_prompt = (
                "Before generating the next beat, think step-by-step about:\n"
                "1. How should the narrative continue given the world's tone and recent events?\n"
                "2. What narrative tension or development is needed?\n"
                "3. How can this beat advance the story while maintaining coherence?\n"
                "4. What specific elements from the world laws and backdrop should influence this beat?\n\n"
                "Provide your reasoning in 2-4 sentences."
            )

            reasoning_messages = messages + [{"role": "user", "content": reasoning_prompt}]

            reasoning_response = await self.client.chat(
                model=model,
                messages=reasoning_messages,
                options={"temperature": 0.5, "num_predict": 300}
            )

            reasoning = reasoning_response['message']['content']

            # Step 2: Stream narrative text using reasoning as context
            generation_messages = messages + [
                {"role": "assistant", "content": reasoning},
                {"role": "user", "content": "Now, write the narrative beat based on your reasoning above."}
            ]

            stream = await self.client.chat(
                model=model,
                messages=generation_messages,
                options=options,
                stream=True
            )

            async for chunk in stream:
                content = chunk['message']['content']
                if content:
                    yield content

            logger.info(
                "beat_streaming_completed",
                story_title=context.story_title
            )

        except Exception as e:
            logger.error("ollama_beat_streaming_error", error=str(e))
            raise RuntimeError(f"Failed to stream beat with Ollama: {str(e)}")

    async def generate_beat_metadata(
        self,
        content: str,
        context: GenerationContext
    ) -> GeneratedBeat:
        """
        Generate metadata (summary, time label, reasoning) for already-generated content.

        Args:
            content: The full beat content that was generated
            context: Narrative context for coherent metadata generation

        Returns:
            GeneratedBeat with empty text field but populated metadata fields
        """
        model = self.model

        logger.info(
            "generating_beat_metadata_with_ollama",
            story_title=context.story_title,
            world_name=context.world_name,
            model=model
        )

        try:
            # HIGH PRIORITY FIX 2.6 & 2.7: Generate summary and determine beat type in parallel
            # with error handling for each task
            summary_task = self.summarize(content)
            beat_type_task = self.determine_beat_type(content, context)

            # Await both tasks with individual error handling
            try:
                summary = await summary_task
            except Exception as e:
                logger.error("summary_task_failed", error=str(e))
                summary = "Summary generation failed."

            try:
                beat_type = await beat_type_task
            except Exception as e:
                logger.error("beat_type_task_failed", error=str(e))
                beat_type = "scene"

            # Determine time label
            local_time_label = BeatGenerationPrompts.build_time_label_prompt(context)

            # Extract world event ID if present
            world_event_id = None
            if context.target_world_event:
                world_event_id = context.target_world_event.get('id')

            # Generate reasoning for this beat
            reasoning_prompt = (
                f"You just generated the following narrative beat:\n\n{content}\n\n"
                "In 2-3 sentences, explain your narrative reasoning: "
                "What was your intent with this beat? How does it advance the story?"
            )

            system_prompt = BeatGenerationPrompts.build_system_prompt(context)

            reasoning_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reasoning_prompt}
            ]

            reasoning_response = await self.client.chat(
                model=model,
                messages=reasoning_messages,
                options={"temperature": 0.5, "num_predict": 200}
            )

            reasoning = reasoning_response['message']['content']

            # Create metadata
            metadata = {
                "model": model,
                "content_length": len(content),
                "word_count": len(content.split())
            }

            logger.info(
                "beat_metadata_generated_successfully",
                story_title=context.story_title,
                beat_type=beat_type
            )

            return GeneratedBeat(
                text="",  # Empty text field as content is already generated
                summary=summary,
                local_time_label=local_time_label,
                reasoning=reasoning,
                world_event_id=world_event_id,
                beat_type=beat_type,
                metadata=metadata
            )

        except Exception as e:
            logger.error("ollama_metadata_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate beat metadata with Ollama: {str(e)}")

    # Entity generation methods

    async def extract_entities(
        self,
        context: EntityExtractionContext,
        config: GenerationConfig
    ) -> List[EntitySuggestion]:
        """
        Extract entities (characters, locations) from narrative text using Ollama.

        Args:
            context: Text to analyze plus world context for coherence
            config: Generation parameters

        Returns:
            List of EntitySuggestion objects with detected entities
        """
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        # CRITICAL FIX 1.1: Validate text is not empty
        if not context.text or not context.text.strip():
            logger.warning(
                "entity_extraction_empty_text",
                world_name=context.world_name
            )
            return []

        # Format existing entities for prompt (limit to first 10-15)
        existing_chars = json.dumps(
            [{"name": c.get("name", "")} for c in context.existing_characters[:10]],
            indent=2
        )
        existing_locs = json.dumps(
            [{"name": l.get("name", "")} for l in context.existing_locations[:10]],
            indent=2
        )

        # CRITICAL FIX 1.4: Null-safe world laws formatting
        world_laws_str = json.dumps(context.world_laws or {}, indent=2)[:500]

        # CRITICAL FIX 1.5: Null-safe world context formatting
        # Build prompt
        prompt = PROMPTS["extract_entities"].format(
            world_name=context.world_name,
            world_tone=context.world_tone,
            world_backdrop=(context.world_backdrop or "")[:500],
            world_laws=world_laws_str,
            existing_characters=existing_chars,
            existing_locations=existing_locs,
            text=context.text,
            confidence_threshold=context.confidence_threshold
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert narrative analyst. Return ONLY valid JSON matching the requested structure."
            },
            {"role": "user", "content": prompt}
        ]

        options = {
            "temperature": 0.3,
            "num_predict": 2000,
        }

        logger.info(
            "extracting_entities_with_ollama",
            world_name=context.world_name,
            model=model,
            text_length=len(context.text)
        )

        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )

            content = response['message']['content']

            # CRITICAL FIX 1.2: Explicit JSON parsing error handling (raise instead of silent return)
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("json_parse_error_extract_entities", error=str(e), content=content[:200])
                raise RuntimeError(f"Failed to parse AI response as JSON: {str(e)}")

            # Convert to EntitySuggestion objects
            suggestions = []

            # CRITICAL FIX 1.3: Validate required fields before accessing
            # Process characters
            for char in result.get("characters", []):
                if "name" not in char:
                    logger.warning("missing_name_in_character", char=char)
                    continue
                suggestions.append(EntitySuggestion(
                    name=char["name"],
                    entity_type="character",
                    description=char.get("description"),
                    confidence=char.get("confidence", 1.0),
                    context_snippet=char.get("context_snippet"),
                    metadata=char.get("metadata", {})
                ))

            # Process locations
            for loc in result.get("locations", []):
                if "name" not in loc:
                    logger.warning("missing_name_in_location", location=loc)
                    continue
                suggestions.append(EntitySuggestion(
                    name=loc["name"],
                    entity_type="location",
                    description=loc.get("description"),
                    confidence=loc.get("confidence", 1.0),
                    context_snippet=loc.get("context_snippet"),
                    metadata=loc.get("metadata", {})
                ))

            logger.info(
                "entities_extracted_successfully",
                world_name=context.world_name,
                num_entities=len(suggestions)
            )

            return suggestions

        except Exception as e:
            logger.error("ollama_entity_extraction_error", error=str(e))
            raise RuntimeError(f"Failed to extract entities with Ollama: {str(e)}")

    async def generate_character(
        self,
        context: CharacterGenerationContext,
        config: GenerationConfig
    ) -> List[EntitySuggestion]:
        """
        Generate character suggestions based on world and story context using Ollama.

        Args:
            context: World context, existing characters, and constraints
            config: Generation parameters

        Returns:
            List of character suggestions (typically 1-3 options)
        """
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        # Format existing characters (limit to first 15)
        existing_chars = json.dumps(
            [
                {
                    "name": c.get("name", ""),
                    "role": c.get("role", ""),
                    "importance": c.get("importance", "")
                }
                for c in context.existing_characters[:15]
            ],
            indent=2
        )

        # Format recent beats for story context (limit to last 5)
        recent_beats_str = ""
        if context.recent_beats:
            recent_beats_str = "\n".join(
                [f"- {beat.get('summary', beat.get('text', '')[:100])}" for beat in context.recent_beats[:5]]
            )

        # Number of suggestions to generate
        num_suggestions = 3

        # CRITICAL FIX 1.4 & 1.5: Null-safe world context formatting
        # Build prompt
        prompt = PROMPTS["generate_character"].format(
            world_name=context.world_name,
            world_tone=context.world_tone,
            world_backdrop=(context.world_backdrop or "")[:500],
            world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
            story_title=context.story_title or "N/A",
            story_synopsis=context.story_synopsis or "N/A",
            recent_beats=recent_beats_str or "N/A",
            existing_characters=existing_chars,
            importance=context.importance or "any",
            role=context.role or "any",
            user_prompt=context.user_prompt or "Generate diverse, interesting characters",
            num_suggestions=num_suggestions
        )

        messages = [
            {
                "role": "system",
                "content": "You are a creative character designer. Return ONLY valid JSON matching the requested structure."
            },
            {"role": "user", "content": prompt}
        ]

        options = {
            "temperature": 0.8,
            "num_predict": 2000,
        }

        logger.info(
            "generating_character_with_ollama",
            world_name=context.world_name,
            model=model,
            importance=context.importance
        )

        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )

            content = response['message']['content']

            # CRITICAL FIX 1.2: Explicit JSON parsing error handling (raise instead of silent return)
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("json_parse_error_generate_character", error=str(e), content=content[:200])
                raise RuntimeError(f"Failed to parse AI response as JSON: {str(e)}")

            # Convert to EntitySuggestion objects
            suggestions = []
            character_list = result if isinstance(result, list) else result.get("characters", [])

            # CRITICAL FIX 1.3: Validate required fields before accessing
            for char in character_list:
                if "name" not in char:
                    logger.warning("missing_name_in_generated_character", char=char)
                    continue
                suggestions.append(EntitySuggestion(
                    name=char["name"],
                    entity_type="character",
                    description=char.get("description", ""),
                    confidence=char.get("confidence", 0.95),
                    metadata=char.get("metadata", {})
                ))

            logger.info(
                "characters_generated_successfully",
                world_name=context.world_name,
                num_characters=len(suggestions)
            )

            return suggestions

        except Exception as e:
            logger.error("ollama_character_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate characters with Ollama: {str(e)}")

    async def generate_location(
        self,
        context: LocationGenerationContext,
        config: GenerationConfig
    ) -> List[EntitySuggestion]:
        """
        Generate location suggestions based on world context using Ollama.

        Args:
            context: World context, existing locations, parent location
            config: Generation parameters

        Returns:
            List of location suggestions (typically 1-3 options)
        """
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        # Format existing locations (limit to first 15)
        existing_locs = json.dumps(
            [
                {
                    "name": l.get("name", ""),
                    "location_type": l.get("location_type", ""),
                    "significance": l.get("significance", "")
                }
                for l in context.existing_locations[:15]
            ],
            indent=2
        )

        # Format parent location
        parent_location_str = "N/A"
        if context.parent_location:
            parent_location_str = json.dumps(
                {
                    "name": context.parent_location.get("name", ""),
                    "description": context.parent_location.get("description", ""),
                    "location_type": context.parent_location.get("location_type", "")
                },
                indent=2
            )

        # Number of suggestions to generate
        num_suggestions = 3

        # CRITICAL FIX 1.4 & 1.5: Null-safe world context formatting
        # Build prompt
        prompt = PROMPTS["generate_location"].format(
            world_name=context.world_name,
            world_tone=context.world_tone,
            world_backdrop=(context.world_backdrop or "")[:500],
            world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
            existing_locations=existing_locs,
            parent_location=parent_location_str,
            location_type=context.location_type or "any",
            significance=context.significance or "any",
            user_prompt=context.user_prompt or "Generate diverse, atmospheric locations",
            num_suggestions=num_suggestions
        )

        messages = [
            {
                "role": "system",
                "content": "You are a creative world-builder. Return ONLY valid JSON matching the requested structure."
            },
            {"role": "user", "content": prompt}
        ]

        options = {
            "temperature": 0.8,
            "num_predict": 2000,
        }

        logger.info(
            "generating_location_with_ollama",
            world_name=context.world_name,
            model=model,
            location_type=context.location_type
        )

        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )

            content = response['message']['content']

            # CRITICAL FIX 1.2: Explicit JSON parsing error handling (raise instead of silent return)
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("json_parse_error_generate_location", error=str(e), content=content[:200])
                raise RuntimeError(f"Failed to parse AI response as JSON: {str(e)}")

            # Convert to EntitySuggestion objects
            suggestions = []
            location_list = result if isinstance(result, list) else result.get("locations", [])

            # CRITICAL FIX 1.3: Validate required fields before accessing
            for loc in location_list:
                if "name" not in loc:
                    logger.warning("missing_name_in_generated_location", location=loc)
                    continue
                suggestions.append(EntitySuggestion(
                    name=loc["name"],
                    entity_type="location",
                    description=loc.get("description", ""),
                    confidence=loc.get("confidence", 0.95),
                    metadata=loc.get("metadata", {})
                ))

            logger.info(
                "locations_generated_successfully",
                world_name=context.world_name,
                num_locations=len(suggestions)
            )

            return suggestions

        except Exception as e:
            logger.error("ollama_location_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate locations with Ollama: {str(e)}")

    async def validate_entity_coherence(
        self,
        context: CoherenceValidationContext,
        config: GenerationConfig
    ) -> CoherenceValidationResult:
        """
        Validate that an entity is coherent with world rules and existing entities using Ollama.

        Args:
            context: Entity to validate plus world context
            config: Generation parameters

        Returns:
            CoherenceValidationResult with issues and suggestions
        """
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        # Format existing entities (limit to first 10)
        existing_chars = json.dumps(
            [{"name": c.get("name", "")} for c in context.existing_characters[:10]],
            indent=2
        )
        existing_locs = json.dumps(
            [{"name": l.get("name", "")} for l in context.existing_locations[:10]],
            indent=2
        )

        # CRITICAL FIX 1.4 & 1.5: Null-safe world context formatting
        # Build prompt
        prompt = PROMPTS["validate_entity_coherence"].format(
            world_name=context.world_name,
            world_tone=context.world_tone,
            world_backdrop=(context.world_backdrop or "")[:500],
            world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
            existing_characters=existing_chars,
            existing_locations=existing_locs,
            entity_type=context.entity_type,
            entity_name=context.entity_name,
            entity_description=context.entity_description or "N/A",
            entity_metadata=json.dumps(context.entity_metadata or {}, indent=2)[:300]
        )

        messages = [
            {
                "role": "system",
                "content": "You are a narrative consistency expert. Return ONLY valid JSON matching the requested structure."
            },
            {"role": "user", "content": prompt}
        ]

        options = {
            "temperature": 0.3,
            "num_predict": 1500,
        }

        logger.info(
            "validating_entity_coherence_with_ollama",
            world_name=context.world_name,
            entity_name=context.entity_name,
            entity_type=context.entity_type,
            model=model
        )

        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )

            content = response['message']['content']

            # Parse JSON response
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("json_parse_error_validate_coherence", error=str(e), content=content[:200])
                # Return default "failed to validate" result
                return CoherenceValidationResult(
                    is_coherent=False,
                    confidence_score=0.0,
                    issues=["Failed to parse validation response"],
                    suggestions=["Please retry validation"],
                    metadata={"error": str(e)}
                )

            # Convert to CoherenceValidationResult
            validation_result = CoherenceValidationResult(
                is_coherent=result.get("is_coherent", False),
                confidence_score=result.get("confidence_score", 0.5),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                metadata=result.get("metadata", {})
            )

            logger.info(
                "entity_coherence_validated",
                world_name=context.world_name,
                entity_name=context.entity_name,
                is_coherent=validation_result.is_coherent,
                confidence_score=validation_result.confidence_score
            )

            return validation_result

        except Exception as e:
            logger.error("ollama_coherence_validation_error", error=str(e))
            raise RuntimeError(f"Failed to validate entity coherence with Ollama: {str(e)}")

    async def enhance_entity_description(
        self,
        entity_name: str,
        entity_type: str,
        current_description: Optional[str],
        world_context: Dict[str, Any],
        config: GenerationConfig
    ) -> str:
        """
        Enhance an entity's description using AI with Ollama.

        Args:
            entity_name: Name of the entity
            entity_type: "character" or "location"
            current_description: Existing description (if any)
            world_context: World name, tone, backdrop, laws
            config: Generation parameters

        Returns:
            Enhanced description text
        """
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        # CRITICAL FIX 1.5: Null-safe backdrop formatting
        # Build prompt
        prompt = PROMPTS["enhance_entity_description"].format(
            world_name=world_context.get("world_name", "Unknown"),
            world_tone=world_context.get("world_tone", ""),
            world_backdrop=(world_context.get("world_backdrop") or "")[:500],
            entity_type=entity_type,
            entity_name=entity_name,
            current_description=current_description or "No description provided yet."
        )

        messages = [
            {
                "role": "system",
                "content": "You are a creative writing specialist. Return ONLY the enhanced description text, no JSON, no explanations."
            },
            {"role": "user", "content": prompt}
        ]

        options = {
            "temperature": 0.7,
            "num_predict": 500,
        }

        logger.info(
            "enhancing_entity_description_with_ollama",
            entity_name=entity_name,
            entity_type=entity_type,
            model=model
        )

        try:
            response = await self.client.chat(
                model=model,
                messages=messages,
                options=options,
            )

            enhanced_description = response['message']['content'].strip()

            logger.info(
                "entity_description_enhanced",
                entity_name=entity_name,
                entity_type=entity_type,
                description_length=len(enhanced_description)
            )

            return enhanced_description

        except Exception as e:
            logger.error("ollama_description_enhancement_error", error=str(e))
            raise RuntimeError(f"Failed to enhance entity description with Ollama: {str(e)}")

    # World Event generation methods

    async def generate_world_event(
        self,
        context: EventGenerationContext,
        config: GenerationConfig
    ) -> List[EventSuggestion]:
        """Generate world event suggestions using Ollama."""
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        logger.info("generating_world_events_with_ollama", world_name=context.world_name)

        try:
            existing_events = json.dumps([{"id": e.get("id"), "summary": e.get("summary"), "t": e.get("t")} for e in context.existing_events[:15]], indent=2)
            existing_chars = json.dumps([{"id": c.get("id"), "name": c.get("name")} for c in context.existing_characters[:15]], indent=2)
            existing_locs = json.dumps([{"id": l.get("id"), "name": l.get("name")} for l in context.existing_locations[:15]], indent=2)

            prompt = PROMPTS["generate_world_event"].format(
                world_name=context.world_name,
                world_tone=context.world_tone,
                world_backdrop=(context.world_backdrop or "")[:500],
                world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
                chronology_mode=context.chronology_mode,
                existing_events=existing_events,
                existing_characters=existing_chars,
                existing_locations=existing_locs,
                event_type=context.event_type or "Not specified",
                time_range_min=context.time_range_min or "Not specified",
                time_range_max=context.time_range_max or "Not specified",
                location_id=context.location_id or "Not specified",
                involving_character_ids=json.dumps(context.involving_character_ids),
                caused_by_event_ids=json.dumps(context.caused_by_event_ids),
                user_prompt=context.user_prompt or "None",
                num_suggestions=3
            )

            messages = [
                {"role": "system", "content": "You are a narrative historian. Return ONLY valid JSON array."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": config.temperature, "num_predict": config.max_tokens}
            )

            content = response['message']['content']
            try:
                result = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error("json_parse_error_generate_event", error=str(e))
                raise RuntimeError(f"Failed to parse AI response: {str(e)}")

            if isinstance(result, dict) and "events" in result:
                result = result["events"]

            suggestions = []
            for event in result if isinstance(result, list) else []:
                if "summary" not in event:
                    continue
                suggestions.append(EventSuggestion(
                    summary=event["summary"],
                    event_type=event.get("event_type", "other"),
                    description=event.get("description", ""),
                    t=float(event.get("t", 0)),
                    label_time=event.get("label_time"),
                    location_hint=event.get("location_hint"),
                    involved_characters=event.get("involved_characters", []),
                    caused_by_hints=event.get("caused_by_hints", []),
                    tags=event.get("tags", []),
                    confidence=event.get("confidence", 0.9),
                    reasoning=event.get("reasoning")
                ))

            return suggestions

        except Exception as e:
            logger.error("ollama_world_event_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate world events with Ollama: {str(e)}")

    async def extract_events_from_beats(
        self,
        context: EventExtractionContext,
        config: GenerationConfig
    ) -> List[EventSuggestion]:
        """Extract world-significant events from story beats using Ollama."""
        from shinkei.generation.prompts import PROMPTS

        if not context.beats:
            return []

        model = config.model or self.model

        try:
            beats_text = json.dumps([{"text": b.get("text", "")[:400], "summary": b.get("summary", "")} for b in context.beats[:8]], indent=2)
            existing_events = json.dumps([{"summary": e.get("summary"), "t": e.get("t")} for e in context.existing_events[:15]], indent=2)

            prompt = PROMPTS["extract_events_from_beats"].format(
                world_name=context.world_name,
                world_tone=context.world_tone,
                world_backdrop=(context.world_backdrop or "")[:500],
                world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
                existing_events=existing_events,
                beats=beats_text,
                confidence_threshold=context.confidence_threshold
            )

            messages = [
                {"role": "system", "content": "You are a narrative analyst. Return ONLY valid JSON array."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": 0.3, "num_predict": config.max_tokens}
            )

            content = response['message']['content']
            result = json.loads(content)

            if isinstance(result, dict) and "events" in result:
                result = result["events"]

            suggestions = []
            for event in result if isinstance(result, list) else []:
                if event.get("confidence", 1.0) < context.confidence_threshold:
                    continue
                if "summary" not in event:
                    continue
                suggestions.append(EventSuggestion(
                    summary=event["summary"],
                    event_type=event.get("event_type", "other"),
                    description=event.get("description", ""),
                    t=float(event.get("t", 0)),
                    label_time=event.get("label_time"),
                    location_hint=event.get("location_hint"),
                    involved_characters=event.get("involved_characters", []),
                    caused_by_hints=event.get("caused_by_hints", []),
                    tags=event.get("tags", []),
                    confidence=event.get("confidence", 0.8),
                    reasoning=event.get("reasoning")
                ))

            return suggestions

        except Exception as e:
            logger.error("ollama_event_extraction_error", error=str(e))
            raise RuntimeError(f"Failed to extract events with Ollama: {str(e)}")

    async def validate_event_coherence(
        self,
        context: EventCoherenceContext,
        config: GenerationConfig
    ) -> CoherenceValidationResult:
        """Validate event coherence with world rules and timeline using Ollama."""
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        try:
            existing_events = json.dumps([{"summary": e.get("summary"), "t": e.get("t")} for e in context.existing_events[:20]], indent=2)
            existing_chars = json.dumps([{"name": c.get("name")} for c in context.existing_characters[:15]], indent=2)
            existing_locs = json.dumps([{"name": l.get("name")} for l in context.existing_locations[:15]], indent=2)

            prompt = PROMPTS["validate_event_coherence"].format(
                world_name=context.world_name,
                world_tone=context.world_tone,
                world_backdrop=(context.world_backdrop or "")[:500],
                world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
                chronology_mode=context.chronology_mode,
                existing_events=existing_events,
                existing_characters=existing_chars,
                existing_locations=existing_locs,
                event_summary=context.event_summary,
                event_type=context.event_type,
                event_t=context.event_t,
                event_description=context.event_description,
                event_location_id=context.event_location_id or "Not specified",
                event_caused_by_ids=json.dumps(context.event_caused_by_ids)
            )

            messages = [
                {"role": "system", "content": "You are a narrative consistency expert. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": 0.3, "num_predict": 1500}
            )

            result = json.loads(response['message']['content'])

            return CoherenceValidationResult(
                is_coherent=result.get("is_coherent", True),
                confidence_score=result.get("confidence_score", 1.0),
                issues=result.get("issues", []),
                suggestions=result.get("suggestions", []),
                metadata=result.get("metadata", {})
            )

        except Exception as e:
            logger.error("ollama_event_validation_error", error=str(e))
            raise RuntimeError(f"Failed to validate event coherence with Ollama: {str(e)}")

    # Story Template generation methods

    async def generate_story_template(
        self,
        context: TemplateGenerationContext,
        config: GenerationConfig
    ) -> GeneratedTemplate:
        """Generate a custom story template using Ollama."""
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        try:
            prompt = PROMPTS["generate_story_template"].format(
                world_name=context.world_name,
                world_tone=context.world_tone,
                world_backdrop=(context.world_backdrop or "")[:500],
                world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
                user_prompt=context.user_prompt or "Create a compelling story template",
                preferred_mode=context.preferred_mode or "Not specified",
                preferred_pov=context.preferred_pov or "Not specified",
                target_length=context.target_length or "Not specified",
                existing_templates=json.dumps(context.existing_templates)
            )

            messages = [
                {"role": "system", "content": "You are a master storyteller. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": config.temperature, "num_predict": config.max_tokens}
            )

            result = json.loads(response['message']['content'])

            return GeneratedTemplate(
                name=result.get("name", "Untitled Template"),
                description=result.get("description", ""),
                synopsis=result.get("synopsis", ""),
                theme=result.get("theme", ""),
                mode=result.get("mode", context.preferred_mode or "collaborative"),
                pov_type=result.get("pov_type", context.preferred_pov or "third"),
                suggested_tags=result.get("suggested_tags", []),
                confidence=result.get("confidence", 0.9),
                reasoning=result.get("reasoning")
            )

        except Exception as e:
            logger.error("ollama_template_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate story template with Ollama: {str(e)}")

    async def generate_story_outline(
        self,
        context: OutlineGenerationContext,
        config: GenerationConfig
    ) -> StoryOutline:
        """Generate a story outline with act/beat structure using Ollama."""
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        try:
            existing_events = json.dumps([{"id": e.get("id"), "summary": e.get("summary")} for e in context.existing_events[:10]], indent=2)
            existing_chars = json.dumps([{"name": c.get("name")} for c in context.existing_characters[:10]], indent=2)
            existing_locs = json.dumps([{"name": l.get("name")} for l in context.existing_locations[:10]], indent=2)

            prompt = PROMPTS["generate_story_outline"].format(
                world_name=context.world_name,
                world_tone=context.world_tone,
                world_backdrop=(context.world_backdrop or "")[:500],
                world_laws=json.dumps(context.world_laws or {}, indent=2)[:500],
                story_title=context.story_title,
                story_synopsis=context.story_synopsis,
                story_theme=context.story_theme or "Not specified",
                num_acts=context.num_acts,
                beats_per_act=context.beats_per_act,
                include_world_events=context.include_world_events,
                existing_events=existing_events,
                existing_characters=existing_chars,
                existing_locations=existing_locs
            )

            messages = [
                {"role": "system", "content": "You are a master story architect. Return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": config.temperature, "num_predict": config.max_tokens}
            )

            result = json.loads(response['message']['content'])

            return StoryOutline(
                acts=result.get("acts", []),
                themes=result.get("themes", []),
                character_arcs=result.get("character_arcs", []),
                estimated_beat_count=result.get("estimated_beat_count", context.num_acts * context.beats_per_act),
                world_events_used=result.get("world_events_used", []),
                metadata=result.get("metadata", {})
            )

        except Exception as e:
            logger.error("ollama_outline_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate story outline with Ollama: {str(e)}")

    async def suggest_templates_for_world(
        self,
        world_name: str,
        world_tone: str,
        world_backdrop: str,
        world_laws: Dict[str, Any],
        config: GenerationConfig
    ) -> List[str]:
        """Suggest appropriate story template types for a world using Ollama."""
        from shinkei.generation.prompts import PROMPTS

        model = config.model or self.model

        try:
            prompt = PROMPTS["suggest_templates_for_world"].format(
                world_name=world_name,
                world_tone=world_tone,
                world_backdrop=(world_backdrop or "")[:500],
                world_laws=json.dumps(world_laws or {}, indent=2)[:500]
            )

            messages = [
                {"role": "system", "content": "You are a genre expert. Return ONLY a valid JSON array of strings."},
                {"role": "user", "content": prompt}
            ]

            response = await self.client.chat(
                model=model,
                messages=messages,
                options={"temperature": 0.5, "num_predict": 500}
            )

            result = json.loads(response['message']['content'])

            if isinstance(result, dict) and "suggestions" in result:
                return result["suggestions"]
            elif isinstance(result, list):
                return result
            return []

        except Exception as e:
            logger.error("ollama_template_suggestion_error", error=str(e))
            raise RuntimeError(f"Failed to suggest templates with Ollama: {str(e)}")
