"""Anthropic provider implementation."""
from typing import AsyncGenerator, Optional
from anthropic import AsyncAnthropic
from shinkei.generation.base import (
    NarrativeModel,
    GenerationRequest,
    GenerationResponse,
    GenerationContext,
    GenerationConfig,
    GeneratedBeat,
    ModificationContext,
    ModifiedBeat
)
from shinkei.generation.beat_prompts import BeatGenerationPrompts
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class AnthropicModel(NarrativeModel):
    """Anthropic implementation of NarrativeModel."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Default model name (optional, defaults to claude-3-5-sonnet-20240620)
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model or "claude-3-5-sonnet-20240620"

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text using Anthropic.
        """
        model = request.model or "claude-3-5-sonnet-20240620"
        
        system = request.system_prompt or ""
        
        response = await self.client.messages.create(
            model=model,
            system=system,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_tokens=request.max_tokens or 1024,
            stop_sequences=request.stop_sequences,
        )

        content = response.content[0].text
        finish_reason = response.stop_reason
        
        usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        return GenerationResponse(
            content=content,
            model_used=response.model,
            usage=usage,
            finish_reason=finish_reason,
        )

    async def stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """
        Stream generated text using Anthropic.
        """
        model = request.model or "claude-3-5-sonnet-20240620"
        system = request.system_prompt or ""

        stream = self.client.messages.create(
            model=model,
            system=system,
            messages=[{"role": "user", "content": request.prompt}],
            temperature=request.temperature,
            max_tokens=request.max_tokens or 1024,
            stop_sequences=request.stop_sequences,
            stream=True,
        )

        async for chunk in stream:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text

    # Narrative-specific methods

    async def generate_next_beat(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> GeneratedBeat:
        """
        Generate next narrative beat using Anthropic Claude.

        Args:
            context: Full narrative context (World + Story + Beats)
            config: Generation parameters

        Returns:
            GeneratedBeat with text, summary, time label, and metadata
        """
        # Build narrative-aware prompts
        system_prompt = BeatGenerationPrompts.build_system_prompt(context)
        user_prompt = BeatGenerationPrompts.build_user_prompt(context)

        # Use model from config, fallback to instance default
        model = config.model or self.model

        logger.info(
            "generating_beat_with_anthropic",
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

            reasoning_response = await self.client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt + "\n\n" + reasoning_prompt}],
                temperature=0.5,  # Lower temperature for coherent reasoning
                max_tokens=300
            )

            reasoning = reasoning_response.content[0].text

            # Step 2: Generate narrative text using reasoning as context
            generation_prompt = f"{user_prompt}\n\nYour reasoning: {reasoning}\n\nNow, write the narrative beat based on your reasoning above."

            response = await self.client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": generation_prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                stop_sequences=config.stop_sequences
            )

            generated_text = response.content[0].text

            # Generate summary
            summary = await self.summarize(generated_text)

            # Determine time label
            local_time_label = BeatGenerationPrompts.build_time_label_prompt(context)

            # Extract world event ID if present
            world_event_id = None
            if context.target_world_event:
                world_event_id = context.target_world_event.get('id')

            # Create metadata
            metadata = {
                "model": response.model,
                "stop_reason": response.stop_reason,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }

            logger.info(
                "beat_generated_successfully",
                story_title=context.story_title,
                output_tokens=metadata["output_tokens"]
            )

            return GeneratedBeat(
                text=generated_text,
                summary=summary,
                local_time_label=local_time_label,
                reasoning=reasoning,
                world_event_id=world_event_id,
                beat_type="scene",
                metadata=metadata
            )

        except Exception as e:
            logger.error("anthropic_beat_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate beat with Anthropic: {str(e)}")

    async def summarize(self, text: str) -> str:
        """
        Generate summary using Anthropic Claude.

        Args:
            text: Narrative text to summarize

        Returns:
            2-3 sentence summary
        """
        prompt = BeatGenerationPrompts.build_summary_prompt(text)

        try:
            response = await self.client.messages.create(
                model=self.model,
                system="You are a concise summarizer. Create brief 2-3 sentence summaries.",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=150  # Short summary
            )

            summary = response.content[0].text.strip()
            return summary

        except Exception as e:
            logger.error("anthropic_summarization_error", error=str(e))
            return "Summary generation failed."

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
            "modifying_beat_with_anthropic",
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

            reasoning_response = await self.client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": reasoning_prompt}],
                temperature=0.5,  # Lower temperature for coherent reasoning
                max_tokens=300
            )

            reasoning = reasoning_response.content[0].text

            # Step 2: Generate modified content
            modification_prompt = (
                f"ORIGINAL BEAT:\n{context.original_content}\n\n"
                f"MODIFICATION INSTRUCTIONS:\n{context.modification_instructions}\n\n"
                f"YOUR REASONING:\n{reasoning}\n\n"
                "Now, rewrite the beat according to the instructions and your reasoning. "
                "Provide ONLY the modified narrative text, without any preamble or explanation."
            )

            response = await self.client.messages.create(
                model=model,
                system=system_prompt,
                messages=[{"role": "user", "content": modification_prompt}],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
            )

            modified_content = response.content[0].text

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

                time_response = await self.client.messages.create(
                    model=model,
                    system="You are a narrative timeline assistant.",
                    messages=[{"role": "user", "content": time_check_prompt}],
                    temperature=0.3,
                    max_tokens=50
                )

                time_result = time_response.content[0].text.strip()
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
                "model": response.model,
                "stop_reason": response.stop_reason,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }

            logger.info(
                "beat_modified_successfully",
                story_title=context.story_title,
                output_tokens=metadata["output_tokens"]
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
            logger.error("anthropic_beat_modification_error", error=str(e))
            raise RuntimeError(f"Failed to modify beat with Anthropic: {str(e)}")
