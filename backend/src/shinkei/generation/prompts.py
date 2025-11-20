"""Centralized prompt templates."""

PROMPTS = {
    "generate_story_ideas": """
You are a creative writing assistant. Generate 3 unique story ideas based on the following theme: {theme}.
Each idea should include a title and a brief synopsis.
Format the output as a JSON list of objects with 'title' and 'synopsis' keys.
""",
    "expand_beat": """
You are a creative writing assistant. Expand the following story beat into a full scene.
Context:
World: {world_name}
Story: {story_title}
Beat: {beat_content}

Write the scene in a compelling narrative style.
""",
    "suggest_beats": """
You are a creative writing assistant. Suggest the next 3 story beats for the following story.
Context:
Story: {story_title}
Current Beats:
{current_beats}

Format the output as a list of beat descriptions.
"""
}
