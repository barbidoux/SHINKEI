"""World templates for quick world creation with preset configurations."""
from typing import Optional
from dataclasses import dataclass
from shinkei.models.world import ChronologyMode


@dataclass
class WorldTemplate:
    """Template for creating a world with predefined settings."""

    name: str
    description: str
    tone: str
    backdrop: str
    laws_physics: str
    laws_metaphysics: str
    laws_social: str
    laws_forbidden: str
    chronology_mode: ChronologyMode


# Template Presets
TEMPLATES = {
    "sci-fi": WorldTemplate(
        name="Sci-Fi Cyberpunk Station",
        description="A sprawling space station in the outer rim, where corporate interests clash with human survival. Neon lights, cybernetic enhancements, and the constant hum of life support systems.",
        tone="Dark, gritty, noir, high-tech low-life",
        backdrop="Year 2287. Nexus Station orbits a dying star in contested corporate space. Three megacorps control life support, food, and security. The undercity thrives in the shadows, where hackers, smugglers, and revolutionaries plot against the corpo elite.",
        laws_physics="FTL travel via jump gates. Artificial gravity through centrifugal force. Cybernetic augmentation common. Hard vacuum kills in seconds. Energy weapons standard.",
        laws_metaphysics="Human consciousness can be digitized and transferred. AI sentience is legally recognized but restricted. Dreams can be recorded and sold. Neural implants blur the line between human and machine.",
        laws_social="Corporate citizenship determines rights. Augmentation stigma in upper classes. Hacking culture celebrates Robin Hood figures. Credits are king. Trust no one.",
        laws_forbidden="No magic. No FTL communication (only travel). No upload immortality (copies, not transfers). No true AI freedom.",
        chronology_mode=ChronologyMode.FRAGMENTED
    ),

    "fantasy": WorldTemplate(
        name="High Fantasy Realm",
        description="A magical realm where ancient dragons soar, elven kingdoms hide in enchanted forests, and human empires rise and fall. Magic flows through ley lines connecting sacred sites.",
        tone="Epic, wonder-filled, mythic, heroic",
        backdrop="The Age of Shattered Crowns. Five kingdoms vie for the vacant Celestial Throne. Dragons have returned after a thousand-year slumber. The Veil between worlds grows thin. Prophecies speak of a chosen one who will either unite or doom the realm.",
        laws_physics="Gravity, fire, water, and earth follow natural laws. Magic can bend but not break physical rules. Healing magic accelerates natural processes. Teleportation requires anchor points. Flight is possible through magic or wings.",
        laws_metaphysics="Souls are real and can be bound or freed. Gods exist and grant power to clerics. Magic draws from ley lines and personal will. True names hold power. Death is not always final—resurrection is rare but possible. Prophecies are mutable.",
        laws_social="Feudal hierarchy. Magic users are both feared and revered. Different races have tense alliances. Honor codes govern knights. Guilds control crafts and trade. Nobility by bloodline, not merit.",
        laws_forbidden="No technology beyond medieval level. No true immortality (lichdom corrupts). No world-ending magic. No time travel. No resurrection without cost.",
        chronology_mode=ChronologyMode.LINEAR
    ),

    "modern": WorldTemplate(
        name="Modern Day Realistic",
        description="Contemporary urban setting where everyday struggles, relationships, and personal growth take center stage. Coffee shops, smartphones, and the complexities of modern life.",
        tone="Grounded, intimate, slice-of-life, bittersweet",
        backdrop="Present day in a mid-sized city. Economic uncertainty, social media anxiety, and the search for meaning in a fast-paced world. People navigate careers, relationships, mental health, and the pressure to 'have it all figured out' by 30.",
        laws_physics="Standard Earth physics. No magic. Technology follows real-world limitations. Medicine is advanced but not miraculous. Death is permanent.",
        laws_metaphysics="No confirmed supernatural elements. Consciousness is biological. Meaning is subjective. Spirituality exists as personal practice, not proven metaphysics.",
        laws_social="Modern democratic society. Social media influences behavior and relationships. Mental health stigma is fading but present. Economic class affects opportunities. Work-life balance is a constant struggle. Authenticity vs. performance.",
        laws_forbidden="No magic. No supernatural elements. No sci-fi technology. Keep it grounded in current reality and human psychology.",
        chronology_mode=ChronologyMode.LINEAR
    ),

    "post-apocalyptic": WorldTemplate(
        name="Post-Apocalyptic Wasteland",
        description="Decades after the collapse of civilization, survivors cluster in fortified settlements. Resources are scarce, trust is scarcer, and hope is the rarest commodity of all.",
        tone="Harsh, survivalist, tense, cautiously hopeful",
        backdrop="30 years after The Event (left ambiguous—could be nuclear war, pandemic, climate collapse, or combination). Nature reclaims cities. Gasoline is liquid gold. Canned food is currency. Scattered communities range from brutal raider gangs to utopian farming communes. Radio signals hint at larger factions.",
        laws_physics="Earth physics apply. No power grid. Solar and wind energy are valuable. Water purification is critical. Radiation may linger in hotspots. Vehicles run on scavenged fuel or biodiesel. Medicine is primitive—antibiotics worth their weight in gold.",
        laws_metaphysics="No magic. Death is common and permanent. Stories and songs keep culture alive. Superstitions arise around The Event. Some believe the world is healing; others think it's dying.",
        laws_social="Survival of the community over individual. Trust is earned through action. Barter economy. Skill determines status—doctors, engineers, farmers are invaluable. Old-world knowledge is precious. Morality is pragmatic—theft for survival is understood, murder is not. Factions range from democratic councils to warlord dictatorships.",
        laws_forbidden="No zombies (unless user specifically wants them). No convenient technology reboots. No easy solutions. Scarcity is real. Violence has consequences. Hope exists but isn't guaranteed.",
        chronology_mode=ChronologyMode.FRAGMENTED
    ),

    "blank": WorldTemplate(
        name="Blank Canvas",
        description="A blank template for building your world from scratch.",
        tone="",
        backdrop="",
        laws_physics="",
        laws_metaphysics="",
        laws_social="",
        laws_forbidden="",
        chronology_mode=ChronologyMode.LINEAR
    )
}


def get_template(template_id: str) -> Optional[WorldTemplate]:
    """Get a world template by its ID."""
    return TEMPLATES.get(template_id)


def list_templates() -> dict[str, dict[str, str]]:
    """List all available templates with basic info."""
    return {
        template_id: {
            "name": template.name,
            "description": template.description,
            "tone": template.tone,
            "chronology_mode": template.chronology_mode.value
        }
        for template_id, template in TEMPLATES.items()
    }
