"""Ollama provider implementation."""
from typing import AsyncGenerator, Optional
from ollama import AsyncClient
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
        model = request.model or "llama3"
        
        # Ollama supports system prompt in options or as a message
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

        response = await self.client.chat(
            model=model,
            messages=messages,
            options=options,
        )

        content = response['message']['content']
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
        model = request.model or "llama3"
        
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
                "model": response.get('model', model),
                "prompt_eval_count": response.get('prompt_eval_count', 0),
                "eval_count": response.get('eval_count', 0),
                "finish_reason": response.get('done_reason', 'stop')
            }

            logger.info(
                "beat_generated_successfully",
                story_title=context.story_title,
                eval_count=metadata["eval_count"]
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
