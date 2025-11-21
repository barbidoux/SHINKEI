"""Unit tests for AuthoringService."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.services.authoring_service import (
    AuthoringService,
    BeatProposal,
    ManualAssistance,
)
from shinkei.models.story import Story, AuthoringMode
from shinkei.models.story_beat import StoryBeat, GeneratedBy
from shinkei.generation.base import GenerationConfig


@pytest_asyncio.fixture
async def mock_session():
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


def setup_mock_story_query(mock_session, story):
    """Helper to setup mock session to return a story from query."""
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = story
    mock_session.execute.return_value = mock_result


@pytest.fixture
def mock_narrative_service():
    """Create a mock NarrativeGenerationService."""
    service = AsyncMock()
    return service


@pytest.fixture
def authoring_service(mock_session, mock_narrative_service):
    """Create an AuthoringService with mocked dependencies."""
    service = AuthoringService(mock_session)
    service.narrative_service = mock_narrative_service
    return service


@pytest.fixture
def mock_story():
    """Create a mock Story object."""
    story = MagicMock(spec=Story)
    story.id = "story-123"
    story.mode = AuthoringMode.AUTONOMOUS
    story.user_id = "user-456"
    return story


@pytest.fixture
def mock_beat():
    """Create a mock StoryBeat object."""
    beat = MagicMock(spec=StoryBeat)
    beat.id = "beat-789"
    beat.content = "This is a test beat content."
    beat.summary = "Test summary"
    beat.local_time_label = "Day 1"
    beat.beat_type = "scene"
    beat.seq_in_story = 1
    beat.generation_reasoning = "Test reasoning"
    beat.generated_by = GeneratedBy.AI
    return beat


class TestAutonomousGenerate:
    """Tests for autonomous_generate method."""

    @pytest.mark.asyncio
    async def test_autonomous_generate_success(
        self, authoring_service, mock_session, mock_narrative_service, mock_story, mock_beat
    ):
        """Test successful autonomous generation."""
        # Setup
        mock_story.mode = AuthoringMode.AUTONOMOUS
        with patch.object(authoring_service, '_get_story', new=AsyncMock(return_value=mock_story)):
            mock_narrative_service.generate_next_beat.return_value = mock_beat

            # Execute
            result = await authoring_service.autonomous_generate(
                story_id="story-123",
                user_id="user-456",
                provider="openai",
                model="gpt-4"
            )

            # Assert
            assert result == mock_beat
            mock_narrative_service.generate_next_beat.assert_called_once()
            call_kwargs = mock_narrative_service.generate_next_beat.call_args[1]
            assert call_kwargs["story_id"] == "story-123"
            assert call_kwargs["user_id"] == "user-456"
            assert call_kwargs["provider"] == "openai"
            assert call_kwargs["model"] == "gpt-4"
            assert call_kwargs["user_instructions"] is None  # No user guidance in autonomous

    @pytest.mark.asyncio
    async def test_autonomous_generate_wrong_mode(
        self, authoring_service, mock_session, mock_story
    ):
        """Test autonomous generation fails when story is not in autonomous mode."""
        # Setup
        mock_story.mode = AuthoringMode.COLLABORATIVE
        setup_mock_story_query(mock_session, mock_story)

        # Execute & Assert
        with pytest.raises(ValueError, match="not autonomous"):
            await authoring_service.autonomous_generate(
                story_id="story-123",
                user_id="user-456"
            )

    @pytest.mark.asyncio
    async def test_autonomous_generate_story_not_found(
        self, authoring_service, mock_session
    ):
        """Test autonomous generation fails when story not found."""
        # Setup
        setup_mock_story_query(mock_session, None)

        # Execute & Assert
        with pytest.raises(ValueError, match="not found"):
            await authoring_service.autonomous_generate(
                story_id="nonexistent",
                user_id="user-456"
            )


class TestCollaborativePropose:
    """Tests for collaborative_propose method."""

    @pytest.mark.asyncio
    async def test_collaborative_propose_success(
        self, authoring_service, mock_session, mock_narrative_service, mock_story, mock_beat
    ):
        """Test successful collaborative proposal generation."""
        # Setup
        mock_story.mode = AuthoringMode.COLLABORATIVE
        setup_mock_story_query(mock_session, mock_story)

        # Create 3 different beats for proposals
        beats = []
        for i in range(3):
            beat = MagicMock(spec=StoryBeat)
            beat.id = f"beat-{i}"
            beat.content = f"Proposal {i} content"
            beat.summary = f"Proposal {i} summary"
            beat.local_time_label = f"Day {i+1}"
            beat.beat_type = "scene"
            beat.generation_reasoning = f"Reasoning {i}"
            beats.append(beat)

        mock_narrative_service.generate_next_beat.side_effect = beats

        # Execute
        result = await authoring_service.collaborative_propose(
            story_id="story-123",
            user_id="user-456",
            user_guidance="Make it exciting",
            num_proposals=3,
            provider="openai"
        )

        # Assert
        assert len(result) == 3
        assert all(isinstance(p, BeatProposal) for p in result)
        assert result[0].content == "Proposal 0 content"
        assert result[1].summary == "Proposal 1 summary"
        assert result[2].reasoning == "Reasoning 2"

        # Verify generate_next_beat called 3 times with varying temperatures
        assert mock_narrative_service.generate_next_beat.call_count == 3

        # Verify beats were deleted from session
        assert mock_session.delete.call_count == 3
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_collaborative_propose_wrong_mode(
        self, authoring_service, mock_session, mock_story
    ):
        """Test collaborative proposal fails when story is not in collaborative mode."""
        # Setup
        mock_story.mode = AuthoringMode.AUTONOMOUS
        setup_mock_story_query(mock_session, mock_story)

        # Execute & Assert
        with pytest.raises(ValueError, match="not collaborative"):
            await authoring_service.collaborative_propose(
                story_id="story-123",
                user_id="user-456"
            )

    @pytest.mark.asyncio
    async def test_collaborative_propose_invalid_num_proposals(
        self, authoring_service, mock_session, mock_story
    ):
        """Test collaborative proposal fails with invalid num_proposals."""
        # Setup
        mock_story.mode = AuthoringMode.COLLABORATIVE
        setup_mock_story_query(mock_session, mock_story)

        # Execute & Assert - Too few
        with pytest.raises(ValueError, match="between 1 and 5"):
            await authoring_service.collaborative_propose(
                story_id="story-123",
                user_id="user-456",
                num_proposals=0
            )

        # Execute & Assert - Too many
        with pytest.raises(ValueError, match="between 1 and 5"):
            await authoring_service.collaborative_propose(
                story_id="story-123",
                user_id="user-456",
                num_proposals=10
            )

    @pytest.mark.asyncio
    async def test_collaborative_propose_with_user_guidance(
        self, authoring_service, mock_session, mock_narrative_service, mock_story, mock_beat
    ):
        """Test collaborative proposal includes user guidance."""
        # Setup
        mock_story.mode = AuthoringMode.COLLABORATIVE
        setup_mock_story_query(mock_session, mock_story)
        mock_narrative_service.generate_next_beat.return_value = mock_beat

        user_guidance = "Focus on character emotions and build suspense"

        # Execute
        result = await authoring_service.collaborative_propose(
            story_id="story-123",
            user_id="user-456",
            user_guidance=user_guidance,
            num_proposals=1
        )

        # Assert
        call_kwargs = mock_narrative_service.generate_next_beat.call_args[1]
        assert call_kwargs["user_instructions"] == user_guidance

    @pytest.mark.asyncio
    async def test_collaborative_propose_handles_partial_failures(
        self, authoring_service, mock_session, mock_narrative_service, mock_story, mock_beat
    ):
        """Test collaborative proposal handles some generation failures gracefully."""
        # Setup
        mock_story.mode = AuthoringMode.COLLABORATIVE
        setup_mock_story_query(mock_session, mock_story)

        # First two succeed, third fails
        mock_narrative_service.generate_next_beat.side_effect = [
            mock_beat,
            mock_beat,
            Exception("Generation failed")
        ]

        # Execute
        result = await authoring_service.collaborative_propose(
            story_id="story-123",
            user_id="user-456",
            num_proposals=3
        )

        # Assert - Should still return 2 successful proposals
        assert len(result) == 2
        assert all(isinstance(p, BeatProposal) for p in result)


class TestManualAssist:
    """Tests for manual_assist method."""

    @pytest.mark.asyncio
    async def test_manual_assist_success(
        self, authoring_service, mock_session, mock_narrative_service, mock_story
    ):
        """Test successful manual assistance."""
        # Setup
        mock_story.mode = AuthoringMode.MANUAL
        setup_mock_story_query(mock_session, mock_story)

        coherence_result = {
            "is_coherent": True,
            "issues": [],
            "suggestions": []
        }
        mock_narrative_service.check_beat_coherence.return_value = coherence_result
        mock_narrative_service.summarize_beat.return_value = "Generated summary"

        user_content = "The protagonist discovers a hidden door."

        # Execute
        result = await authoring_service.manual_assist(
            story_id="story-123",
            user_id="user-456",
            user_content=user_content,
            provider="openai"
        )

        # Assert
        assert isinstance(result, ManualAssistance)
        assert result.coherence_result == coherence_result
        assert result.suggested_summary == "Generated summary"
        assert result.world_event_suggestions == []  # Currently empty

        # Verify coherence check called
        mock_narrative_service.check_beat_coherence.assert_called_once()
        coherence_kwargs = mock_narrative_service.check_beat_coherence.call_args[1]
        assert coherence_kwargs["beat_content"] == user_content

        # Verify summarize called
        mock_narrative_service.summarize_beat.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_assist_wrong_mode_warning(
        self, authoring_service, mock_session, mock_narrative_service, mock_story
    ):
        """Test manual assist works but logs warning for non-manual mode."""
        # Setup
        mock_story.mode = AuthoringMode.AUTONOMOUS
        setup_mock_story_query(mock_session, mock_story)

        coherence_result = {"is_coherent": True, "issues": [], "suggestions": []}
        mock_narrative_service.check_beat_coherence.return_value = coherence_result
        mock_narrative_service.summarize_beat.return_value = "Summary"

        # Execute - Should still work even for non-manual mode
        result = await authoring_service.manual_assist(
            story_id="story-123",
            user_id="user-456",
            user_content="Test content"
        )

        # Assert
        assert isinstance(result, ManualAssistance)
        # No exception raised, just a warning logged

    @pytest.mark.asyncio
    async def test_manual_assist_coherence_failure(
        self, authoring_service, mock_session, mock_narrative_service, mock_story
    ):
        """Test manual assist handles coherence check failure gracefully."""
        # Setup
        mock_story.mode = AuthoringMode.MANUAL
        setup_mock_story_query(mock_session, mock_story)

        mock_narrative_service.check_beat_coherence.side_effect = Exception("Coherence check failed")
        mock_narrative_service.summarize_beat.return_value = "Summary"

        # Execute
        result = await authoring_service.manual_assist(
            story_id="story-123",
            user_id="user-456",
            user_content="Test content"
        )

        # Assert - Should still return result with error in coherence
        assert isinstance(result, ManualAssistance)
        assert result.coherence_result.get("is_coherent") is None
        assert "error" in result.coherence_result
        assert result.suggested_summary == "Summary"  # Summary should still work

    @pytest.mark.asyncio
    async def test_manual_assist_summary_failure(
        self, authoring_service, mock_session, mock_narrative_service, mock_story
    ):
        """Test manual assist handles summary generation failure gracefully."""
        # Setup
        mock_story.mode = AuthoringMode.MANUAL
        setup_mock_story_query(mock_session, mock_story)

        coherence_result = {"is_coherent": True, "issues": [], "suggestions": []}
        mock_narrative_service.check_beat_coherence.return_value = coherence_result
        mock_narrative_service.summarize_beat.side_effect = Exception("Summary failed")

        # Execute
        result = await authoring_service.manual_assist(
            story_id="story-123",
            user_id="user-456",
            user_content="Test content"
        )

        # Assert - Should still return result with empty summary
        assert isinstance(result, ManualAssistance)
        assert result.coherence_result == coherence_result  # Coherence should still work
        assert result.suggested_summary == ""  # Empty on failure


class TestBeatProposal:
    """Tests for BeatProposal class."""

    def test_beat_proposal_creation(self):
        """Test BeatProposal can be created with all fields."""
        proposal = BeatProposal(
            id="proposal-1",
            content="Test content",
            summary="Test summary",
            local_time_label="Day 1",
            beat_type="scene",
            reasoning="Test reasoning"
        )

        assert proposal.id == "proposal-1"
        assert proposal.content == "Test content"
        assert proposal.summary == "Test summary"
        assert proposal.local_time_label == "Day 1"
        assert proposal.beat_type == "scene"
        assert proposal.reasoning == "Test reasoning"

    def test_beat_proposal_to_dict(self):
        """Test BeatProposal can be converted to dictionary."""
        proposal = BeatProposal(
            id="proposal-1",
            content="Test content",
            summary="Test summary",
            local_time_label="Day 1",
            beat_type="scene",
            reasoning="Test reasoning"
        )

        result = proposal.to_dict()

        assert result["id"] == "proposal-1"
        assert result["content"] == "Test content"
        assert result["summary"] == "Test summary"
        assert result["local_time_label"] == "Day 1"
        assert result["beat_type"] == "scene"
        assert result["reasoning"] == "Test reasoning"


class TestManualAssistance:
    """Tests for ManualAssistance class."""

    def test_manual_assistance_creation(self):
        """Test ManualAssistance can be created with all fields."""
        coherence = {"is_coherent": True, "issues": []}
        assistance = ManualAssistance(
            coherence_result=coherence,
            suggested_summary="Test summary",
            world_event_suggestions=["event-1", "event-2"]
        )

        assert assistance.coherence_result == coherence
        assert assistance.suggested_summary == "Test summary"
        assert len(assistance.world_event_suggestions) == 2

    def test_manual_assistance_to_dict(self):
        """Test ManualAssistance can be converted to dictionary."""
        coherence = {"is_coherent": True, "issues": []}
        assistance = ManualAssistance(
            coherence_result=coherence,
            suggested_summary="Test summary",
            world_event_suggestions=["event-1"]
        )

        result = assistance.to_dict()

        assert result["coherence"] == coherence
        assert result["suggested_summary"] == "Test summary"
        assert result["world_event_suggestions"] == ["event-1"]
