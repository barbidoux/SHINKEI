"""Narrative-aware prompts for beat generation."""
from shinkei.generation.base import GenerationContext


class BeatGenerationPrompts:
    """Prompt templates for narrative beat generation."""

    @staticmethod
    def build_system_prompt(context: GenerationContext) -> str:
        """
        Build system prompt establishing world and narrative rules.

        Creates a comprehensive prompt that instructs the AI about:
        - World tone, backdrop, and laws
        - Story synopsis and POV
        - Authoring mode (autonomous/collaborative/manual)
        - Writing style guidelines

        Args:
            context: Generation context with world and story data

        Returns:
            System prompt string
        """
        return f"""You are a creative narrative engine for the world "{context.world_name}".

WORLD CONTEXT:
- Tone: {context.world_tone}
- Backdrop: {context.world_backdrop}

WORLD LAWS (MUST BE RESPECTED):
{BeatGenerationPrompts._format_laws(context.world_laws)}

STORY CONTEXT:
- Title: {context.story_title}
- Synopsis: {context.story_synopsis}
- POV: {context.story_pov_type}

YOUR ROLE:
You are writing the next narrative beat in this story. Your writing must:
1. Respect all world laws absolutely
2. Match the established tone perfectly
3. Continue naturally from recent events
4. Be engaging and well-written
5. Show, don't tell (use vivid, sensory details)
6. Maintain the specified POV consistently

{BeatGenerationPrompts._build_mode_instructions(context.story_mode)}

Write in a literary style appropriate for {context.world_tone} narratives."""

    @staticmethod
    def build_user_prompt(context: GenerationContext) -> str:
        """
        Build user prompt with specific generation instructions.

        Includes:
        - Recent beats for continuity
        - Target WorldEvent (if any)
        - User instructions (for collaborative mode)
        - Generation constraints (length, pacing, tension)

        Args:
            context: Generation context

        Returns:
            User prompt string
        """
        prompt_parts = []

        # Add recent beats for continuity
        if context.recent_beats:
            prompt_parts.append("RECENT NARRATIVE BEATS:")
            for i, beat in enumerate(context.recent_beats[-3:], 1):
                summary = beat.get('summary', beat.get('content', '')[:100])
                time_label = beat.get('local_time_label', 'Unknown time')
                prompt_parts.append(f"\n{i}. {summary}")
                prompt_parts.append(f"   Time: {time_label}")

        # Add target event if specified
        if context.target_world_event:
            prompt_parts.append(f"\n\nTARGET EVENT:")
            prompt_parts.append(f"- Time: {context.target_world_event.get('label_time', 'Unknown')}")
            prompt_parts.append(f"- Event: {context.target_world_event.get('summary', '')}")
            prompt_parts.append(f"- Type: {context.target_world_event.get('type', 'event')}")
            prompt_parts.append(f"- Location: {context.target_world_event.get('location', 'Unknown')}")

        # Add user instructions if in collaborative mode
        if context.user_instructions:
            prompt_parts.append(f"\n\nUSER GUIDANCE:")
            prompt_parts.append(context.user_instructions)

        # Add generation constraints
        constraints = []
        if context.target_length:
            constraints.append(f"LENGTH: Aim for approximately {context.target_length} words")

        if constraints:
            prompt_parts.append("\n\nLENGTH CONSTRAINT:")
            for constraint in constraints:
                prompt_parts.append(f"- {constraint}")

        # Add narrative style instructions
        style_instructions = BeatGenerationPrompts._build_narrative_style_instructions(context)
        if style_instructions:
            prompt_parts.append(style_instructions)

        # Final instruction
        prompt_parts.append("\n\nWrite the next narrative beat:")

        return "\n".join(prompt_parts)

    @staticmethod
    def _format_laws(laws: dict) -> str:
        """
        Format world laws for prompt.

        Args:
            laws: Dictionary with physics, metaphysics, social, forbidden keys

        Returns:
            Formatted laws string
        """
        formatted = []

        if laws.get("physics"):
            formatted.append(f"- Physics: {laws['physics']}")
        if laws.get("metaphysics"):
            formatted.append(f"- Metaphysics: {laws['metaphysics']}")
        if laws.get("social"):
            formatted.append(f"- Social: {laws['social']}")
        if laws.get("forbidden"):
            formatted.append(f"- FORBIDDEN (NEVER include): {laws['forbidden']}")

        return "\n".join(formatted) if formatted else "No specific laws defined"

    @staticmethod
    def _build_narrative_style_instructions(context: GenerationContext) -> str:
        """
        Build narrative style instructions based on context settings.

        Args:
            context: Generation context with style parameters

        Returns:
            Formatted style instructions string
        """
        instructions = []

        # Pacing
        if context.pacing:
            pacing_details = {
                "slow": "Take time to develop scenes with deliberate details, internal reflection, and atmospheric description. Allow moments to breathe.",
                "medium": "Balance scene development with forward momentum. Provide enough detail for immersion while keeping the story moving.",
                "fast": "Keep the narrative moving with action, quick scene transitions, and concise prose. Focus on events and reactions."
            }
            instructions.append(f"PACING ({context.pacing.upper()}): {pacing_details.get(context.pacing, '')}")

        # Tension level
        if context.tension_level:
            tension_details = {
                "low": "Maintain a calm, relaxed atmosphere. Focus on character moments, world-building, or quiet progression.",
                "medium": "Build engaging anticipation without overwhelming. Create interest and mild suspense to keep readers invested.",
                "high": "Create intense, gripping moments that keep readers on edge. Use conflict, stakes, and urgency to drive tension."
            }
            instructions.append(f"TENSION ({context.tension_level.upper()}): {tension_details.get(context.tension_level, '')}")

        # Dialogue density
        if context.dialogue_density:
            dialogue_details = {
                "minimal": "Focus on narration with occasional dialogue only for key moments. Let the prose carry the story.",
                "moderate": "Balance narration and dialogue naturally. Use conversation when it advances character or plot.",
                "heavy": "Use conversation as a primary storytelling device. Rich dialogue exchanges reveal character and advance the story."
            }
            instructions.append(f"DIALOGUE ({context.dialogue_density.upper()}): {dialogue_details.get(context.dialogue_density, '')}")

        # Description richness
        if context.description_richness:
            description_details = {
                "sparse": "Keep descriptions concise and functional. Focus on essential details that drive the narrative.",
                "balanced": "Provide sufficient sensory and environmental detail without over-describing. Paint the scene adequately.",
                "detailed": "Create rich, immersive descriptions that bring scenes to life. Engage all senses and build vivid imagery."
            }
            instructions.append(f"DESCRIPTION ({context.description_richness.upper()}): {description_details.get(context.description_richness, '')}")

        if instructions:
            return "\n\nNARRATIVE STYLE:\n" + "\n".join(f"- {inst}" for inst in instructions)
        return ""

    @staticmethod
    def _build_mode_instructions(mode: str) -> str:
        """
        Build mode-specific instructions.

        Args:
            mode: autonomous/collaborative/manual

        Returns:
            Mode-specific instruction string
        """
        if mode == "autonomous":
            return """MODE: AUTONOMOUS
Generate the narrative continuation freely while respecting all constraints.
Focus on compelling storytelling and natural progression."""

        elif mode == "collaborative":
            return """MODE: COLLABORATIVE
Generate narrative that incorporates user guidance while maintaining quality and coherence.
The user may edit your output, so prioritize clarity and adaptability."""

        else:  # manual
            return """MODE: MANUAL ASSISTANCE
This will be reviewed and edited by the user.
Focus on coherence validation and providing a solid foundation."""

    @staticmethod
    def build_summary_prompt(text: str) -> str:
        """
        Build prompt for generating a beat summary.

        Args:
            text: Full narrative text to summarize

        Returns:
            Prompt for summarization
        """
        return f"""Summarize this narrative beat in 2-3 concise sentences.
Focus on the key events, character actions, and narrative progression.
Avoid subjective interpretation - stick to what happens.

TEXT:
{text}

SUMMARY:"""

    @staticmethod
    def build_time_label_prompt(context: GenerationContext) -> str:
        """
        Build prompt for generating an in-world time label.

        Args:
            context: Generation context

        Returns:
            Prompt for time label generation
        """
        if context.target_world_event:
            return context.target_world_event.get('label_time', 'Unknown Time')

        # Suggest format based on recent beats
        if context.recent_beats:
            last_label = context.recent_beats[-1].get('local_time_label', '')
            if last_label:
                return f"Continue from: {last_label}"

        # Default suggestions based on tone
        if 'journal' in context.story_mode.lower() or 'log' in context.world_tone.lower():
            beat_count = len(context.recent_beats) + 1
            return f"Log {beat_count:04d}"
        elif 'chapter' in context.story_mode.lower():
            beat_count = len(context.recent_beats) + 1
            return f"Chapter {beat_count}"
        else:
            beat_count = len(context.recent_beats) + 1
            return f"Beat {beat_count}"
