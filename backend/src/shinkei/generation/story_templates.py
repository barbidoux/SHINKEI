"""Story templates for quick story creation with preset configurations."""
from typing import Optional
from dataclasses import dataclass
from shinkei.models.story import AuthoringMode, POVType


@dataclass
class StoryTemplate:
    """Template for creating a story with predefined settings."""

    name: str
    description: str
    synopsis: str
    theme: str
    mode: AuthoringMode
    pov_type: POVType
    suggested_tags: list[str]


# Template Presets
TEMPLATES = {
    "sci-fi-thriller": StoryTemplate(
        name="Sci-Fi Thriller",
        description="A suspenseful science fiction mystery set in space or future tech environments",
        synopsis="In the depths of space (or a high-tech facility), something has gone terribly wrong. As the investigation unfolds, dark secrets emerge that threaten everything.",
        theme="Mystery, paranoia, technological hubris",
        mode=AuthoringMode.COLLABORATIVE,
        pov_type=POVType.THIRD,
        suggested_tags=["sci-fi", "thriller", "mystery", "suspense"]
    ),

    "epic-fantasy-quest": StoryTemplate(
        name="Epic Fantasy Quest",
        description="A hero's journey through a magical realm filled with ancient powers and legendary conflicts",
        synopsis="Called by destiny (or prophecy, or circumstance), a hero must embark on a perilous quest to save the realm from an ancient evil. Along the way, allies are found, enemies are made, and the true nature of heroism is discovered.",
        theme="Heroism, sacrifice, destiny vs. free will",
        mode=AuthoringMode.COLLABORATIVE,
        pov_type=POVType.THIRD,
        suggested_tags=["fantasy", "epic", "quest", "adventure", "magic"]
    ),

    "slice-of-life": StoryTemplate(
        name="Slice of Life",
        description="Character-driven contemporary drama focusing on everyday experiences and personal growth",
        synopsis="In the rhythm of daily life, small moments accumulate into meaningful change. Through relationships, challenges, and quiet revelations, a character discovers what truly matters.",
        theme="Identity, relationships, personal growth, finding meaning in the mundane",
        mode=AuthoringMode.MANUAL,
        pov_type=POVType.FIRST,
        suggested_tags=["slice-of-life", "contemporary", "drama", "character-study"]
    ),

    "survival-horror": StoryTemplate(
        name="Survival Horror",
        description="Post-apocalyptic or isolated survival story with horror elements",
        synopsis="In a world transformed by catastrophe (or in a place cut off from civilization), survival is not guaranteed. As resources dwindle and threats multiply, the line between human and monster blurs.",
        theme="Survival, humanity under pressure, hope vs. despair",
        mode=AuthoringMode.COLLABORATIVE,
        pov_type=POVType.FIRST,
        suggested_tags=["horror", "survival", "post-apocalyptic", "thriller"]
    ),

    "mystery-detective": StoryTemplate(
        name="Mystery Detective",
        description="Classic detective procedural with puzzle-solving and investigation",
        synopsis="When a crime shatters the peace, a detective (professional or reluctant) must piece together clues, interview suspects, and unravel a web of deception to find the truth.",
        theme="Truth, justice, the complexity of human nature",
        mode=AuthoringMode.COLLABORATIVE,
        pov_type=POVType.THIRD,
        suggested_tags=["mystery", "detective", "crime", "investigation"]
    ),

    "romantic-drama": StoryTemplate(
        name="Romantic Drama",
        description="Relationship-focused story exploring love, connection, and emotional conflict",
        synopsis="Two people, brought together by circumstance or fate, navigate the complexities of connection. As they grow closer, past wounds and present challenges test whether love can truly overcome all.",
        theme="Love, vulnerability, emotional healing, sacrifice",
        mode=AuthoringMode.MANUAL,
        pov_type=POVType.FIRST,
        suggested_tags=["romance", "drama", "relationship", "emotional"]
    ),

    "coming-of-age": StoryTemplate(
        name="Coming of Age",
        description="Personal growth journey through transformative experiences and self-discovery",
        synopsis="At a crossroads in life, a young person must navigate unfamiliar territory—new responsibilities, difficult choices, and the realization that the world is more complex than they thought. Through trials and revelations, they discover who they truly are.",
        theme="Identity, growth, loss of innocence, finding one's place",
        mode=AuthoringMode.MANUAL,
        pov_type=POVType.FIRST,
        suggested_tags=["coming-of-age", "drama", "self-discovery", "growth"]
    ),

    "action-adventure": StoryTemplate(
        name="Action Adventure",
        description="Fast-paced adventure with high stakes and thrilling action sequences",
        synopsis="When danger strikes and time is running out, a hero (or team) must race against impossible odds. Through daring action, narrow escapes, and pulse-pounding confrontations, they fight to save what matters most.",
        theme="Courage, perseverance, friendship, overcoming odds",
        mode=AuthoringMode.AUTONOMOUS,
        pov_type=POVType.THIRD,
        suggested_tags=["action", "adventure", "thriller", "fast-paced"]
    ),

    "blank": StoryTemplate(
        name="Blank Canvas",
        description="Start from scratch with no preset elements",
        synopsis="",
        theme="",
        mode=AuthoringMode.MANUAL,
        pov_type=POVType.THIRD,
        suggested_tags=[]
    ),
}


def get_template(template_id: str) -> Optional[StoryTemplate]:
    """
    Get a story template by ID.

    Args:
        template_id: Template identifier

    Returns:
        StoryTemplate instance or None if not found
    """
    return TEMPLATES.get(template_id)


def list_templates() -> dict[str, dict[str, str]]:
    """
    List all available story templates with summary information.

    Returns:
        Dictionary mapping template IDs to summary info
    """
    return {
        template_id: {
            "name": template.name,
            "description": template.description,
            "mode": template.mode.value,
            "pov_type": template.pov_type.value,
            "suggested_tags": template.suggested_tags
        }
        for template_id, template in TEMPLATES.items()
    }


def get_template_names() -> list[str]:
    """
    Get list of all template IDs.

    Returns:
        List of template identifier strings
    """
    return list(TEMPLATES.keys())
