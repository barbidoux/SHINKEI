# 🤖 **SHINKEI - AI ENGINE & FRONTEND DETAILED IMPLEMENTATION GUIDE**

## **Supplementary Document to Main Implementation Plan**
## **Version:** 1.0.0

---

# **PART I: AI ENGINE DETAILED IMPLEMENTATION (PHASE 4-5)**

## **PHASE 4: AI ENGINE FOUNDATION - DETAILED WALKTHROUGH**

### **MILESTONE 4.1: Abstract NarrativeModel Interface**

#### **Core Architecture Philosophy**

The AI engine must be:
1. **Provider-agnostic**: Work with any LLM (local or API-based)
2. **Swappable**: Change models without code changes
3. **Observable**: Log all interactions for debugging
4. **Testable**: Easy to mock for unit tests
5. **Resilient**: Handle API failures gracefully

---

#### **Step 4.1.1: Base Interface (`backend/src/shinkei/ai/models/base.py`)**

```python
"""Base interface for narrative models."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass
class GenerationConfig:
    """Configuration for text generation."""
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None


@dataclass
class GeneratedBeat:
    """Result of beat generation."""
    text: str
    summary: str
    local_time_label: str
    world_event_id: Optional[str] = None
    beat_type: str = "scene"
    metadata: Dict[str, Any] = None


@dataclass
class GenerationContext:
    """Context for narrative generation."""
    # World context
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]
    
    # Story context
    story_title: str
    story_synopsis: str
    story_pov_type: str
    story_mode: str
    
    # Recent beats for continuity
    recent_beats: List[Dict[str, Any]]
    
    # Target event (if any)
    target_world_event: Optional[Dict[str, Any]] = None
    
    # User instructions (for collaborative mode)
    user_instructions: Optional[str] = None
    
    # Generation constraints
    target_length: Optional[int] = None
    pacing: Optional[str] = None  # "slow", "medium", "fast"
    tension_level: Optional[str] = None  # "low", "medium", "high"


class NarrativeModel(ABC):
    """
    Abstract base class for all narrative generation models.
    
    This interface ensures all AI backends (OpenAI, Anthropic, local models)
    implement the same methods and can be swapped transparently.
    """
    
    def __init__(self, provider: ModelProvider, model_name: str, **kwargs):
        """
        Initialize the narrative model.
        
        Args:
            provider: Model provider type
            model_name: Specific model identifier
            **kwargs: Provider-specific configuration
        """
        self.provider = provider
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    async def generate_next_beat(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> GeneratedBeat:
        """
        Generate the next story beat based on context.
        
        Args:
            context: Full generation context
            config: Generation parameters
            
        Returns:
            Generated beat with text and metadata
        """
        pass
    
    @abstractmethod
    async def summarize(self, text: str) -> str:
        """
        Generate a concise summary of narrative text.
        
        Args:
            text: Text to summarize
            
        Returns:
            Summary (2-3 sentences)
        """
        pass
    
    @abstractmethod
    async def extract_entities(
        self,
        text: str
    ) -> Dict[str, List[str]]:
        """
        Extract narrative entities from text.
        
        Args:
            text: Narrative text
            
        Returns:
            Dict with keys: "characters", "locations", "concepts"
        """
        pass
    
    @abstractmethod
    async def validate_coherence(
        self,
        new_text: str,
        context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Validate that new text is coherent with world/story context.
        
        Args:
            new_text: New narrative text to validate
            context: World and story context
            
        Returns:
            Dict with "is_coherent": bool and "issues": List[str]
        """
        pass
    
    @abstractmethod
    async def generate_suggestions(
        self,
        context: GenerationContext,
        num_suggestions: int = 3
    ) -> List[str]:
        """
        Generate multiple narrative suggestions (for collaborative mode).
        
        Args:
            context: Generation context
            num_suggestions: Number of suggestions to generate
            
        Returns:
            List of narrative suggestions
        """
        pass
    
    def health_check(self) -> bool:
        """
        Check if the model is available and responding.
        
        Returns:
            True if healthy, False otherwise
        """
        return True
```

---

#### **Step 4.1.2: OpenAI Implementation (`backend/src/shinkei/ai/models/openai_model.py`)**

```python
"""OpenAI-based narrative model implementation."""
import openai
from typing import Optional, Dict, Any, List
from src.shinkei.ai.models.base import (
    NarrativeModel,
    GenerationContext,
    GenerationConfig,
    GeneratedBeat,
    ModelProvider
)
from src.shinkei.ai.prompts.beat_generation import BeatGenerationPrompts
from src.shinkei.config import settings
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class OpenAINarrativeModel(NarrativeModel):
    """OpenAI GPT-based narrative generation."""
    
    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None
    ):
        """
        Initialize OpenAI model.
        
        Args:
            model_name: OpenAI model identifier
            api_key: Optional API key (uses settings if not provided)
        """
        super().__init__(ModelProvider.OPENAI, model_name)
        
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        openai.api_key = self.api_key
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        
        logger.info(
            "openai_model_initialized",
            model=model_name
        )
    
    async def generate_next_beat(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> GeneratedBeat:
        """Generate next beat using OpenAI."""
        
        # Build system prompt
        system_prompt = BeatGenerationPrompts.build_system_prompt(context)
        
        # Build user prompt
        user_prompt = BeatGenerationPrompts.build_user_prompt(context)
        
        try:
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                stop=config.stop_sequences
            )
            
            # Extract generated text
            generated_text = response.choices[0].message.content
            
            # Generate summary
            summary = await self.summarize(generated_text)
            
            # Extract time label from context or generate
            local_time_label = self._determine_time_label(context)
            
            logger.info(
                "beat_generated_successfully",
                story_id=context.story_title,
                tokens=response.usage.total_tokens
            )
            
            return GeneratedBeat(
                text=generated_text,
                summary=summary,
                local_time_label=local_time_label,
                world_event_id=context.target_world_event.get("id") if context.target_world_event else None,
                beat_type="scene",
                metadata={
                    "model": self.model_name,
                    "tokens_used": response.usage.total_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
        except openai.OpenAIError as e:
            logger.error("openai_generation_error", error=str(e))
            raise RuntimeError(f"Failed to generate beat: {str(e)}")
    
    async def summarize(self, text: str) -> str:
        """Generate summary using OpenAI."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise summarizer. Create a 2-3 sentence summary of the narrative text."
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this narrative:\n\n{text}"
                    }
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except openai.OpenAIError as e:
            logger.error("openai_summarization_error", error=str(e))
            return "Summary generation failed."
    
    async def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities using OpenAI."""
        
        prompt = f"""Extract narrative entities from this text.
Return a JSON object with three keys:
- "characters": list of character names
- "locations": list of location names
- "concepts": list of important concepts or themes

Text: {text}

Return only valid JSON, no markdown formatting."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an entity extraction expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            import json
            entities = json.loads(response.choices[0].message.content)
            
            return {
                "characters": entities.get("characters", []),
                "locations": entities.get("locations", []),
                "concepts": entities.get("concepts", [])
            }
            
        except (openai.OpenAIError, json.JSONDecodeError) as e:
            logger.error("entity_extraction_error", error=str(e))
            return {"characters": [], "locations": [], "concepts": []}
    
    async def validate_coherence(
        self,
        new_text: str,
        context: GenerationContext
    ) -> Dict[str, Any]:
        """Validate coherence using OpenAI."""
        
        prompt = f"""Validate if this new narrative text is coherent with the established world and story.

World Context:
- Name: {context.world_name}
- Tone: {context.world_tone}
- Backdrop: {context.world_backdrop}
- Laws: {context.world_laws}

Story Context:
- Title: {context.story_title}
- Synopsis: {context.story_synopsis}

New Text:
{new_text}

Return a JSON object with:
- "is_coherent": boolean
- "issues": list of coherence issues (empty if coherent)
- "suggestions": list of improvement suggestions

Return only valid JSON."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a narrative coherence validator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            return result
            
        except (openai.OpenAIError, json.JSONDecodeError) as e:
            logger.error("coherence_validation_error", error=str(e))
            return {
                "is_coherent": True,  # Default to accepting on error
                "issues": [],
                "suggestions": []
            }
    
    async def generate_suggestions(
        self,
        context: GenerationContext,
        num_suggestions: int = 3
    ) -> List[str]:
        """Generate multiple suggestions using OpenAI."""
        
        suggestions = []
        
        # Generate each suggestion independently
        for i in range(num_suggestions):
            try:
                beat = await self.generate_next_beat(
                    context,
                    GenerationConfig(temperature=0.8 + (i * 0.1))  # Vary temperature
                )
                suggestions.append(beat.text)
            except Exception as e:
                logger.error("suggestion_generation_error", error=str(e), index=i)
                continue
        
        return suggestions
    
    def _determine_time_label(self, context: GenerationContext) -> str:
        """Determine appropriate time label for the beat."""
        
        if context.target_world_event:
            return context.target_world_event.get("label_time", "Unknown Time")
        
        # Generate based on story mode
        if context.story_mode == "journal":
            beat_count = len(context.recent_beats)
            return f"Entry {beat_count + 1:03d}"
        else:
            return f"Chapter {len(context.recent_beats) + 1}"
    
    def health_check(self) -> bool:
        """Check OpenAI API availability."""
        try:
            import httpx
            import asyncio
            
            async def check():
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=5.0
                    )
                    return response.status_code == 200
            
            return asyncio.run(check())
            
        except Exception as e:
            logger.error("openai_health_check_failed", error=str(e))
            return False
```

---

#### **Step 4.1.3: Prompt Engineering Utilities (`backend/src/shinkei/ai/prompts/beat_generation.py`)**

```python
"""Prompts for narrative beat generation."""
from src.shinkei.ai.models.base import GenerationContext


class BeatGenerationPrompts:
    """Prompt templates for beat generation."""
    
    @staticmethod
    def build_system_prompt(context: GenerationContext) -> str:
        """
        Build system prompt establishing world and narrative rules.
        
        Args:
            context: Generation context
            
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
1. Respect all world laws
2. Match the established tone
3. Continue naturally from recent events
4. Be engaging and well-written
5. Show, don't tell
6. Use vivid, sensory details

{BeatGenerationPrompts._build_mode_instructions(context.story_mode)}

Write in a literary style appropriate for {context.world_tone} narratives."""

    @staticmethod
    def build_user_prompt(context: GenerationContext) -> str:
        """
        Build user prompt with specific generation instructions.
        
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
                prompt_parts.append(f"\n{i}. {beat.get('summary', '')}")
                prompt_parts.append(f"   Time: {beat.get('local_time_label', '')}")
        
        # Add target event if specified
        if context.target_world_event:
            prompt_parts.append(f"\n\nTARGET EVENT:")
            prompt_parts.append(f"- Time: {context.target_world_event['label_time']}")
            prompt_parts.append(f"- Event: {context.target_world_event['summary']}")
            prompt_parts.append(f"- Type: {context.target_world_event['type']}")
        
        # Add user instructions if in collaborative mode
        if context.user_instructions:
            prompt_parts.append(f"\n\nUSER GUIDANCE:")
            prompt_parts.append(context.user_instructions)
        
        # Add generation constraints
        if context.target_length:
            prompt_parts.append(f"\n\nLENGTH: Approximately {context.target_length} words")
        
        if context.pacing:
            prompt_parts.append(f"PACING: {context.pacing}")
        
        if context.tension_level:
            prompt_parts.append(f"TENSION: {context.tension_level}")
        
        # Final instruction
        prompt_parts.append("\n\nWrite the next narrative beat:")
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def _format_laws(laws: dict) -> str:
        """Format world laws for prompt."""
        formatted = []
        
        if laws.get("physics"):
            formatted.append(f"- Physics: {laws['physics']}")
        if laws.get("metaphysics"):
            formatted.append(f"- Metaphysics: {laws['metaphysics']}")
        if laws.get("social"):
            formatted.append(f"- Social: {laws['social']}")
        if laws.get("forbidden"):
            formatted.append(f"- FORBIDDEN: {laws['forbidden']}")
        
        return "\n".join(formatted) if formatted else "No specific laws defined"
    
    @staticmethod
    def _build_mode_instructions(mode: str) -> str:
        """Build mode-specific instructions."""
        
        if mode == "auto":
            return """MODE: AUTONOMOUS
Generate the narrative continuation freely while respecting all constraints."""
        
        elif mode == "collab":
            return """MODE: COLLABORATIVE
Generate narrative that incorporates user guidance while maintaining quality and coherence."""
        
        else:  # manual
            return """MODE: MANUAL ASSISTANCE
This will be reviewed and edited by the user. Focus on coherence validation."""
```

---

#### **Step 4.1.4: Model Factory (`backend/src/shinkei/ai/factory.py`)**

```python
"""Factory for creating narrative model instances."""
from typing import Optional
from src.shinkei.ai.models.base import NarrativeModel, ModelProvider
from src.shinkei.ai.models.openai_model import OpenAINarrativeModel
# from src.shinkei.ai.models.anthropic_model import AnthropicNarrativeModel
# from src.shinkei.ai.models.local_model import LocalNarrativeModel
from src.shinkei.config import settings
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class ModelFactory:
    """Factory for creating narrative model instances."""
    
    _models_cache = {}
    
    @classmethod
    def create_model(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> NarrativeModel:
        """
        Create a narrative model instance.
        
        Args:
            provider: Model provider (openai, anthropic, local, ollama)
            model_name: Specific model identifier
            **kwargs: Provider-specific configuration
            
        Returns:
            Configured NarrativeModel instance
        """
        
        # Use default provider if not specified
        provider = provider or settings.default_llm_provider
        
        # Create cache key
        cache_key = f"{provider}:{model_name}"
        
        # Return cached model if available
        if cache_key in cls._models_cache:
            logger.debug("model_retrieved_from_cache", key=cache_key)
            return cls._models_cache[cache_key]
        
        # Create new model instance
        try:
            if provider == "openai":
                model = OpenAINarrativeModel(
                    model_name=model_name or "gpt-4-turbo-preview",
                    **kwargs
                )
            
            elif provider == "anthropic":
                # model = AnthropicNarrativeModel(
                #     model_name=model_name or "claude-3-opus-20240229",
                #     **kwargs
                # )
                raise NotImplementedError("Anthropic model coming soon")
            
            elif provider in ["local", "ollama"]:
                # model = LocalNarrativeModel(
                #     model_name=model_name or "mistral",
                #     **kwargs
                # )
                raise NotImplementedError("Local models coming soon")
            
            else:
                raise ValueError(f"Unsupported provider: {provider}")
            
            # Cache the model
            cls._models_cache[cache_key] = model
            
            logger.info("model_created", provider=provider, model=model_name)
            return model
            
        except Exception as e:
            logger.error("model_creation_failed", provider=provider, error=str(e))
            raise
    
    @classmethod
    def clear_cache(cls):
        """Clear the model cache."""
        cls._models_cache.clear()
        logger.info("model_cache_cleared")
```

---

#### **Unit Tests for AI Engine**

**Test File: `backend/tests/unit/test_ai_models.py`**
```python
"""Unit tests for AI models."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.shinkei.ai.models.base import GenerationContext, GenerationConfig
from src.shinkei.ai.models.openai_model import OpenAINarrativeModel


@pytest.fixture
def sample_context():
    """Sample generation context."""
    return GenerationContext(
        world_name="Test World",
        world_tone="mysterious",
        world_backdrop="A strange place",
        world_laws={"physics": "normal", "metaphysics": "dreams can be real"},
        story_title="Test Story",
        story_synopsis="A test narrative",
        story_pov_type="omniscient",
        story_mode="auto",
        recent_beats=[]
    )


@pytest.fixture
def sample_config():
    """Sample generation config."""
    return GenerationConfig(temperature=0.7, max_tokens=1000)


@pytest.mark.asyncio
async def test_openai_model_initialization():
    """Test OpenAI model can be initialized."""
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        model = OpenAINarrativeModel(api_key="test-key")
        assert model.provider == "openai"
        assert model.model_name == "gpt-4-turbo-preview"


@pytest.mark.asyncio
async def test_generate_next_beat_mock(sample_context, sample_config):
    """Test beat generation with mocked API."""
    with patch('openai.AsyncOpenAI') as mock_client:
        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated narrative text"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 100
        
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        model = OpenAINarrativeModel(api_key="test-key")
        
        with patch.object(model, 'summarize', return_value="Summary"):
            beat = await model.generate_next_beat(sample_context, sample_config)
        
        assert beat.text == "Generated narrative text"
        assert beat.summary == "Summary"
        assert beat.metadata["tokens_used"] == 100


@pytest.mark.asyncio
async def test_summarize_mock():
    """Test summarization with mocked API."""
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test summary"
        
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        model = OpenAINarrativeModel(api_key="test-key")
        summary = await model.summarize("Long text to summarize")
        
        assert summary == "Test summary"
```

---

## **PHASE 5: NARRATIVE GENERATION PIPELINE**

### **MILESTONE 5.1: Generation Service**

#### **Step 5.1.1: Generation Service (`backend/src/shinkei/services/generation_service.py`)**

```python
"""Service for managing narrative generation."""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from src.shinkei.ai.factory import ModelFactory
from src.shinkei.ai.models.base import GenerationContext, GenerationConfig, GeneratedBeat
from src.shinkei.models.story import Story, AuthoringMode
from src.shinkei.models.story_beat import StoryBeat, GeneratedBy
from src.shinkei.models.world_event import WorldEvent
from src.shinkei.repositories.story import StoryRepository
from src.shinkei.repositories.story_beat import StoryBeatRepository
from src.shinkei.repositories.world_event import WorldEventRepository
from src.shinkei.logging_config import get_logger

logger = get_logger(__name__)


class GenerationService:
    """Service for orchestrating narrative generation."""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize generation service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.story_repo = StoryRepository(session)
        self.beat_repo = StoryBeatRepository(session)
        self.event_repo = WorldEventRepository(session)
    
    async def generate_next_beat(
        self,
        story_id: str,
        user_instructions: Optional[str] = None,
        target_event_id: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None
    ) -> StoryBeat:
        """
        Generate the next beat for a story.
        
        Args:
            story_id: Story UUID
            user_instructions: Optional user guidance (collaborative mode)
            target_event_id: Optional specific WorldEvent to write about
            generation_config: Optional generation parameters
            
        Returns:
            Created StoryBeat
        """
        
        # Load story and context
        story = await self.story_repo.get_by_id(story_id)
        if not story:
            raise ValueError(f"Story not found: {story_id}")
        
        # Build generation context
        context = await self._build_context(
            story,
            user_instructions=user_instructions,
            target_event_id=target_event_id
        )
        
        # Get model instance
        model = ModelFactory.create_model()
        
        # Set default config if not provided
        if not generation_config:
            generation_config = GenerationConfig()
        
        # Generate beat
        logger.info("generating_beat", story_id=story_id, mode=story.mode)
        
        try:
            generated = await model.generate_next_beat(context, generation_config)
            
            # Determine next sequence number
            last_beat = await self.beat_repo.get_last_beat(story_id)
            next_seq = (last_beat.seq_in_story + 1) if last_beat else 1
            
            # Create StoryBeat
            beat = StoryBeat(
                story_id=story_id,
                seq_in_story=next_seq,
                world_event_id=generated.world_event_id,
                local_time_label=generated.local_time_label,
                type=generated.beat_type,
                text=generated.text,
                summary=generated.summary,
                generated_by=GeneratedBy.AI
            )
            
            self.session.add(beat)
            await self.session.flush()
            await self.session.refresh(beat)
            
            logger.info(
                "beat_generated_and_saved",
                story_id=story_id,
                beat_id=beat.id,
                seq=next_seq
            )
            
            return beat
            
        except Exception as e:
            logger.error("beat_generation_failed", story_id=story_id, error=str(e))
            raise
    
    async def _build_context(
        self,
        story: Story,
        user_instructions: Optional[str] = None,
        target_event_id: Optional[str] = None
    ) -> GenerationContext:
        """
        Build generation context from story and world data.
        
        Args:
            story: Story instance
            user_instructions: Optional user guidance
            target_event_id: Optional target event ID
            
        Returns:
            GenerationContext instance
        """
        
        # Load world
        world = story.world
        
        # Load recent beats
        recent_beats = await self.beat_repo.get_recent_beats(story.id, limit=5)
        recent_beats_data = [
            {
                "text": beat.text,
                "summary": beat.summary,
                "local_time_label": beat.local_time_label
            }
            for beat in recent_beats
        ]
        
        # Load target event if specified
        target_event = None
        if target_event_id:
            event = await self.event_repo.get_by_id(target_event_id)
            if event:
                target_event = {
                    "id": event.id,
                    "t": event.t,
                    "label_time": event.label_time,
                    "summary": event.summary,
                    "type": event.type
                }
        
        return GenerationContext(
            world_name=world.name,
            world_tone=world.tone or "",
            world_backdrop=world.backdrop or "",
            world_laws=world.laws,
            story_title=story.title,
            story_synopsis=story.synopsis_start or "",
            story_pov_type=story.pov_type.value,
            story_mode=story.mode.value,
            recent_beats=recent_beats_data,
            target_world_event=target_event,
            user_instructions=user_instructions
        )
```

---

This supplementary guide continues with detailed implementations for:
- Frontend architecture with SvelteKit
- State management patterns
- Component library
- Routing and navigation
- API client with error handling
- Authentication flow
- Real-time updates

The complete guide would be approximately 5000+ more lines covering all frontend aspects, multi-mode authoring UIs, and production deployment strategies.