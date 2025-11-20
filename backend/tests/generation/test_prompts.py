"""Tests for generation prompt templates."""
import pytest
from shinkei.generation.prompts import PROMPTS


class TestPrompts:
    """Tests for PROMPTS dictionary and template functionality."""

    def test_prompts_dict_exists(self):
        """Test that PROMPTS dictionary exists."""
        assert PROMPTS is not None
        assert isinstance(PROMPTS, dict)

    def test_prompts_dict_not_empty(self):
        """Test that PROMPTS dictionary is not empty."""
        assert len(PROMPTS) > 0

    def test_expected_prompt_keys_exist(self):
        """Test that expected prompt keys are present."""
        expected_keys = [
            "generate_story_ideas",
            "expand_beat",
            "suggest_beats"
        ]

        for key in expected_keys:
            assert key in PROMPTS, f"Expected prompt key '{key}' not found"

    def test_all_prompts_are_strings(self):
        """Test that all prompt values are strings."""
        for key, value in PROMPTS.items():
            assert isinstance(value, str), f"Prompt '{key}' is not a string"

    def test_all_prompts_are_non_empty(self):
        """Test that all prompt values are non-empty."""
        for key, value in PROMPTS.items():
            assert len(value.strip()) > 0, f"Prompt '{key}' is empty"


class TestGenerateStoryIdeasPrompt:
    """Tests for generate_story_ideas prompt template."""

    def test_generate_story_ideas_prompt_exists(self):
        """Test that generate_story_ideas prompt exists."""
        assert "generate_story_ideas" in PROMPTS

    def test_generate_story_ideas_has_theme_placeholder(self):
        """Test that prompt has theme placeholder."""
        prompt = PROMPTS["generate_story_ideas"]
        assert "{theme}" in prompt

    def test_generate_story_ideas_format_with_theme(self):
        """Test formatting prompt with theme."""
        prompt = PROMPTS["generate_story_ideas"]
        formatted = prompt.format(theme="Science Fiction")

        assert "Science Fiction" in formatted
        assert "{theme}" not in formatted

    def test_generate_story_ideas_format_with_empty_theme(self):
        """Test formatting prompt with empty theme."""
        prompt = PROMPTS["generate_story_ideas"]
        formatted = prompt.format(theme="")

        assert "{theme}" not in formatted
        assert "Generate 3 unique story ideas" in formatted

    def test_generate_story_ideas_format_missing_context_raises(self):
        """Test that formatting without theme raises KeyError."""
        prompt = PROMPTS["generate_story_ideas"]

        with pytest.raises(KeyError):
            prompt.format()


class TestExpandBeatPrompt:
    """Tests for expand_beat prompt template."""

    def test_expand_beat_prompt_exists(self):
        """Test that expand_beat prompt exists."""
        assert "expand_beat" in PROMPTS

    def test_expand_beat_has_required_placeholders(self):
        """Test that prompt has all required placeholders."""
        prompt = PROMPTS["expand_beat"]

        assert "{world_name}" in prompt
        assert "{story_title}" in prompt
        assert "{beat_content}" in prompt

    def test_expand_beat_format_with_all_context(self):
        """Test formatting prompt with all context."""
        prompt = PROMPTS["expand_beat"]
        formatted = prompt.format(
            world_name="Cyberpunk Tokyo",
            story_title="Neon Dreams",
            beat_content="The protagonist enters the underground market."
        )

        assert "Cyberpunk Tokyo" in formatted
        assert "Neon Dreams" in formatted
        assert "The protagonist enters the underground market." in formatted
        assert "{world_name}" not in formatted
        assert "{story_title}" not in formatted
        assert "{beat_content}" not in formatted

    def test_expand_beat_format_missing_world_name_raises(self):
        """Test that formatting without world_name raises KeyError."""
        prompt = PROMPTS["expand_beat"]

        with pytest.raises(KeyError):
            prompt.format(
                story_title="Test Story",
                beat_content="Test content"
            )

    def test_expand_beat_format_missing_story_title_raises(self):
        """Test that formatting without story_title raises KeyError."""
        prompt = PROMPTS["expand_beat"]

        with pytest.raises(KeyError):
            prompt.format(
                world_name="Test World",
                beat_content="Test content"
            )

    def test_expand_beat_format_missing_beat_content_raises(self):
        """Test that formatting without beat_content raises KeyError."""
        prompt = PROMPTS["expand_beat"]

        with pytest.raises(KeyError):
            prompt.format(
                world_name="Test World",
                story_title="Test Story"
            )


class TestSuggestBeatsPrompt:
    """Tests for suggest_beats prompt template."""

    def test_suggest_beats_prompt_exists(self):
        """Test that suggest_beats prompt exists."""
        assert "suggest_beats" in PROMPTS

    def test_suggest_beats_has_required_placeholders(self):
        """Test that prompt has all required placeholders."""
        prompt = PROMPTS["suggest_beats"]

        assert "{story_title}" in prompt
        assert "{current_beats}" in prompt

    def test_suggest_beats_format_with_all_context(self):
        """Test formatting prompt with all context."""
        prompt = PROMPTS["suggest_beats"]
        current_beats = """
        1. The hero receives a mysterious letter
        2. The hero meets an old mentor
        3. The hero discovers a hidden artifact
        """

        formatted = prompt.format(
            story_title="The Lost Kingdom",
            current_beats=current_beats
        )

        assert "The Lost Kingdom" in formatted
        assert "The hero receives a mysterious letter" in formatted
        assert "{story_title}" not in formatted
        assert "{current_beats}" not in formatted

    def test_suggest_beats_format_with_empty_beats(self):
        """Test formatting prompt with empty current_beats."""
        prompt = PROMPTS["suggest_beats"]

        formatted = prompt.format(
            story_title="New Story",
            current_beats=""
        )

        assert "New Story" in formatted
        assert "{current_beats}" not in formatted

    def test_suggest_beats_format_missing_story_title_raises(self):
        """Test that formatting without story_title raises KeyError."""
        prompt = PROMPTS["suggest_beats"]

        with pytest.raises(KeyError):
            prompt.format(current_beats="Some beats")

    def test_suggest_beats_format_missing_current_beats_raises(self):
        """Test that formatting without current_beats raises KeyError."""
        prompt = PROMPTS["suggest_beats"]

        with pytest.raises(KeyError):
            prompt.format(story_title="Test Story")


class TestPromptTemplateIntegrity:
    """Tests for overall prompt template integrity."""

    def test_no_unintended_placeholders(self):
        """Test that prompts don't have unintended placeholders."""
        # Only these placeholders are expected
        allowed_placeholders = {
            "theme",
            "world_name",
            "story_title",
            "beat_content",
            "current_beats"
        }

        for key, prompt in PROMPTS.items():
            # Find all placeholders in the format {something}
            import re
            placeholders = re.findall(r'\{(\w+)\}', prompt)

            for placeholder in placeholders:
                assert placeholder in allowed_placeholders, \
                    f"Unexpected placeholder '{placeholder}' in prompt '{key}'"

    def test_prompts_have_instructions(self):
        """Test that all prompts contain instruction text."""
        for key, prompt in PROMPTS.items():
            # Each prompt should mention being a creative writing assistant
            assert "creative writing assistant" in prompt.lower() or \
                   "assistant" in prompt.lower(), \
                   f"Prompt '{key}' doesn't have clear instructions"

    def test_prompts_maintain_consistent_style(self):
        """Test that prompts maintain consistent style."""
        for key, prompt in PROMPTS.items():
            # Each prompt should start with a clear role definition
            assert prompt.strip().startswith("You are") or \
                   prompt.strip().startswith("#") or \
                   "assistant" in prompt.lower(), \
                   f"Prompt '{key}' doesn't start with role definition"
