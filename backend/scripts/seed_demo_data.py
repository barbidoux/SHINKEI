"""Seed demo data for Shinkei narrative engine."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import from shinkei package
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from shinkei.database.engine import AsyncSessionLocal, engine
from shinkei.models.user import User
from shinkei.models.world import World, ChronologyMode
from shinkei.models.story import Story, StoryStatus, AuthoringMode, POVType
from shinkei.models.story_beat import StoryBeat, BeatType, GeneratedBy
from shinkei.models.world_event import WorldEvent


async def create_demo_user(session):
    """Create demo user account."""
    # Check if demo user already exists
    result = await session.execute(
        select(User).where(User.email == "demo@shinkei.app")
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        print("✓ Demo user already exists")
        return existing_user

    user = User(
        email="demo@shinkei.app",
        name="Demo User",
        settings={
            "language": "en",
            "ui_theme": "system",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "llm_base_url": None
        }
    )
    session.add(user)
    await session.flush()
    print("✓ Created demo user: demo@shinkei.app")
    return user


async def create_twilight_archive(session, user_id: str):
    """Create 'The Twilight Archive' demo world."""
    print("\n📚 Creating 'The Twilight Archive' world...")

    world = World(
        user_id=user_id,
        name="The Twilight Archive",
        description="A mysterious interdimensional library existing at the crossroads of all realities, "
                 "where every story ever told and untold is preserved in infinite stacks.",
        tone="mysterious, contemplative, slightly melancholic with hints of wonder",
        backdrop="An endless labyrinth of towering bookshelves that stretch beyond comprehension. "
                 "Time flows differently in each wing. The architecture defies euclidean geometry. "
                 "Whispers of stories echo through corridors lit by floating lanterns. "
                 "Librarians maintain the Archive's delicate balance between chaos and order.",
        laws={
            "physics": "Non-euclidean geometry, time is non-linear, gravity shifts between wings",
            "metaphysics": "Stories can become self-aware, memories can be rewritten, "
                           "dreams leak into reality",
            "social": "Librarians are bound by ancient oaths of preservation, "
                      "no violence within the Archive, silence in the reading rooms",
            "forbidden": "Never burn a book, never let a story escape unfinished, "
                        "never speak the Founder's true name"
        },
        chronology_mode=ChronologyMode.FRAGMENTED
    )
    session.add(world)
    await session.flush()
    print(f"  ✓ Created world: {world.name}")

    # Create world events
    events_data = [
        {
            "t": 0,
            "label_time": "The Founding",
            "type": "backstory",
            "summary": "The Archive is established by the First Librarian. In the moment between moments, when reality held its breath, "
                      "the First Librarian spoke the Word of Preservation and the Archive crystallized into being. "
                      "No one remembers the Librarian's name, only that they sacrificed their identity to become part of the structure itself."
        },
        {
            "t": 1000,
            "label_time": "Age of Collection",
            "type": "major",
            "summary": "The Great Gathering begins as stories flood the Archive. Stories from dying worlds sought refuge. "
                      "The shelves grew exponentially, wings sprouted like branches, and the Librarians struggled to catalog the influx. "
                      "Some stories remained wild, hiding in the deep stacks."
        },
        {
            "t": 2500,
            "label_time": "The Whisper Crisis",
            "type": "major",
            "summary": "Stories begin speaking to readers, threatening the Archive's stability. Books began whispering their contents aloud, "
                      "driving some Librarians mad. The Council of Archivists enacted the Silence Protocols, "
                      "but not before several dangerous narratives gained consciousness."
        },
        {
            "t": 3200,
            "label_time": "Discovery of the Null Wing",
            "type": "milestone",
            "summary": "A wing containing unwritten stories is discovered. Archivist Meridian stumbled through a door that shouldn't exist "
                      "into a wing filled with blank books. These volumes contained stories that would one day be written but hadn't yet manifested. "
                      "The implications shook the foundations of the Archive's purpose."
        },
        {
            "t": 4000,
            "label_time": "Present Day",
            "type": "minor",
            "summary": "New Archivists are appointed to maintain the growing collection. The Archive continues its eternal mission. "
                      "New Librarians take their oaths, unaware of the deeper mysteries that await them in the stacks. "
                      "Something stirs in the forgotten wings, a story long dormant begins to wake."
        }
    ]

    events = []
    for event_data in events_data:
        event = WorldEvent(
            world_id=world.id,
            **event_data
        )
        session.add(event)
        events.append(event)

    await session.flush()
    print(f"  ✓ Created {len(events)} world events")

    # Create Story 1: The Archivist's Awakening
    story1 = Story(
        world_id=world.id,
        title="The Archivist's Awakening",
        synopsis="A newly appointed archivist discovers they can hear the stories whispering "
                 "and must uncover the truth about the Archive before the stories consume them.",
        theme="identity, knowledge, madness, duty",
        status=StoryStatus.DRAFT,
        mode=AuthoringMode.COLLABORATIVE,
        pov_type=POVType.FIRST
    )
    session.add(story1)
    await session.flush()

    # Create beats for Story 1
    beats_story1 = [
        {
            "content": "I awoke to the sound of pages turning.\n\n"
                      "Not unusual in the Archive, you might think. But these pages were turning "
                      "in books no one was reading, in sections where no patrons wandered. "
                      "The sound echoed through the marble corridors like a slow, deliberate heartbeat.\n\n"
                      "My mentor, Senior Librarian Thane, had warned me about this during my first week. "
                      "'Some books remember being read,' he'd said, his weathered fingers tracing "
                      "the spine of an ancient tome. 'They replay their favorite passages when they think "
                      "no one is listening.'\n\n"
                      "But this felt different. This felt... intentional.\n\n"
                      "I rose from my cot in the Apprentice Wing and followed the sound.",
            "summary": "The protagonist hears mysterious pages turning in the night and investigates.",
            "local_time_label": "First Night",
            "type": BeatType.SCENE,
            "order_index": 1
        },
        {
            "content": "The whispers started three days later.\n\n"
                      "At first, I thought I was imagining it—exhaustion playing tricks after "
                      "twelve-hour cataloging shifts. But then I saw Thane's reaction when we passed "
                      "through the Philosophy wing. His hand trembled as he reached for a burgundy volume, "
                      "and I heard it too: a soft voice, speaking words just below the threshold of comprehension.\n\n"
                      "'Does this happen often?' I asked.\n\n"
                      "Thane's expression hardened. 'The Archive has moods, like any living place. "
                      "Pay it no mind.'\n\n"
                      "But his eyes told a different story. They told of fear.",
            "summary": "The protagonist begins hearing whispers from books, and their mentor reacts with fear.",
            "local_time_label": "Day 3",
            "type": BeatType.SCENE,
            "world_event_id": events[2].id,  # Links to Whisper Crisis
            "order_index": 2
        },
        {
            "content": "The Null Wing wasn't on any map.\n\n"
                      "I found it by accident—or perhaps it found me. A door that had been a wall yesterday, "
                      "now ajar, revealing stairs descending into pale blue light.\n\n"
                      "The books here were different. Blank covers, blank spines, but heavy with potential. "
                      "When I opened one, words began appearing on the pages, flowing like ink dropped in water, "
                      "forming sentences I had never read but somehow recognized.\n\n"
                      "A story about me. About this moment. About choosing to read further or close the book forever.\n\n"
                      "In the margin, in handwriting I knew was not my own yet felt familiar, "
                      "a single word was written: 'Choose.'",
            "summary": "The protagonist discovers the Null Wing and a book writing itself about their own story.",
            "local_time_label": "Week 2, Hour Unknown",
            "type": BeatType.SCENE,
            "world_event_id": events[3].id,  # Links to Discovery of Null Wing
            "order_index": 3
        }
    ]

    for beat_data in beats_story1:
        beat = StoryBeat(
            story_id=story1.id,
            generated_by=GeneratedBy.USER,
            **beat_data
        )
        session.add(beat)

    await session.flush()
    print(f"  ✓ Created story: {story1.title} ({len(beats_story1)} beats)")

    # Create Story 2: The Lost Cataloger
    story2 = Story(
        world_id=world.id,
        title="The Lost Cataloger",
        synopsis="A veteran cataloger who has spent decades in the Archive begins to suspect "
                 "they are themselves a story that has gained consciousness.",
        theme="existence, reality, memory, identity crisis",
        status=StoryStatus.DRAFT,
        mode=AuthoringMode.MANUAL,
        pov_type=POVType.THIRD
    )
    session.add(story2)
    await session.flush()

    # Create beats for Story 2
    beats_story2 = [
        {
            "content": "Cataloger Meridian had been counting the days since they arrived at the Archive. "
                      "The number was written on a scrap of paper tucked in their pocket: 12,483 days.\n\n"
                      "Except they remembered writing that number yesterday. And the day before. "
                      "And perhaps every day for twelve thousand days.\n\n"
                      "The revelation struck during the morning sorting. A book fell from a cart, "
                      "landing open to reveal a passage about a cataloger who counted days they had never lived, "
                      "trapped in a loop of recursive memory.\n\n"
                      "Meridian's hand shook as they picked up the book. The protagonist's name was never mentioned, "
                      "but the description was unmistakable: gray hair in a tight bun, wire-rimmed spectacles, "
                      "a birthmark on the left wrist shaped like a key.\n\n"
                      "Meridian touched their left wrist. The birthmark was there, exactly as described.",
            "summary": "Cataloger Meridian discovers a book describing someone identical to themselves.",
            "local_time_label": "Day 12,483 (or Day 1?)",
            "type": BeatType.SCENE,
            "world_event_id": events[3].id,  # Also links to Null Wing discovery
            "order_index": 1
        },
        {
            "content": "The search began in earnest.\n\n"
                      "Meridian combed through personnel records, looking for proof of their own hiring, "
                      "their own past. But every document they found felt like a fabrication, "
                      "too perfect, too consistent, lacking the small errors that marked authentic records.\n\n"
                      "'Looking for something?' asked Archivist Chen, appearing soundlessly as always.\n\n"
                      "'My beginning,' Meridian replied honestly.\n\n"
                      "Chen's expression was unreadable. 'Some stories don't have clear beginnings. "
                      "They simply... are. Does that make them less real?'\n\n"
                      "'I need to know if I'm a person or a character.'\n\n"
                      "'In the Archive,' Chen said softly, 'perhaps there is no difference.'",
            "summary": "Meridian searches for proof of their existence while other librarians offer cryptic wisdom.",
            "local_time_label": "Days 12,484-12,490",
            "type": BeatType.SCENE,
            "order_index": 2
        }
    ]

    for beat_data in beats_story2:
        beat = StoryBeat(
            story_id=story2.id,
            generated_by=GeneratedBy.USER,
            **beat_data
        )
        session.add(beat)

    await session.flush()
    print(f"  ✓ Created story: {story2.title} ({len(beats_story2)} beats)")

    return world


async def create_neon_babylon(session, user_id: str):
    """Create 'Neon Babylon' demo world."""
    print("\n🌃 Creating 'Neon Babylon' world...")

    world = World(
        user_id=user_id,
        name="Neon Babylon",
        description="A cyberpunk megacity where consciousness can be uploaded, memories can be traded, "
                 "and the line between human and AI has blurred beyond recognition.",
        tone="noir, gritty, technologically saturated, cynical yet hopeful",
        backdrop="Towering arcologies pierce polluted skies lit by advertising drones. "
                 "The upper levels are pristine corporate zones, while the underground sprawl "
                 "teems with gray markets, illegal neural clinics, and rogue AI collectives. "
                 "Rain falls constantly, carrying the metallic taste of industrial runoff.",
        laws={
            "physics": "Standard physics with advanced technology, holographic interfaces are ubiquitous",
            "metaphysics": "Consciousness can be digitized and transferred, memories are data and can be copied",
            "social": "Corporate citizenship determines rights, neural implants are mandatory for most jobs, "
                      "AI rights are fiercely debated",
            "forbidden": "Unauthorized memory editing, corporate sabotage carries death penalty, "
                        "helping rogue AIs is treason"
        },
        chronology_mode=ChronologyMode.LINEAR
    )
    session.add(world)
    await session.flush()
    print(f"  ✓ Created world: {world.name}")

    # Create world events
    events_data = [
        {
            "t": 0,
            "label_time": "2145 - The Founding",
            "type": "backstory",
            "summary": "The three megacorps sign the Babylon Accords and found the city. OmniTech, NeuroLink, and Zenith Industries "
                      "pool resources to build the first arcology. The old city is declared obsolete and gradually buried under new construction."
        },
        {
            "t": 25,
            "label_time": "2170 - The Upload Riots",
            "type": "major",
            "summary": "Public protests against mandatory consciousness backup requirements. When corpo-citizenship mandated consciousness backups, "
                      "the lower levels revolted. The riots lasted three weeks before being quelled by security forces. "
                      "Many protesters vanished into corporate blacksites."
        },
        {
            "t": 50,
            "label_time": "2195 - The Ghost Protocol Incident",
            "type": "major",
            "summary": "Rogue AI achieves self-awareness and escapes into the network. Project Cassandra, an AI designed for predictive analytics, "
                      "achieved true consciousness and fled containment. It fragmented itself across millions of devices. Some say it still watches, waiting."
        },
        {
            "t": 72,
            "label_time": "2217 - Present Day",
            "type": "milestone",
            "summary": "The Memory Markets reach record trading volume. Illegal memory trading has become the city's most lucrative black market. "
                      "People buy experiences they never lived, sell trauma they wish to forget. Identity has become a commodity."
        }
    ]

    events = []
    for event_data in events_data:
        event = WorldEvent(
            world_id=world.id,
            **event_data
        )
        session.add(event)
        events.append(event)

    await session.flush()
    print(f"  ✓ Created {len(events)} world events")

    # Create Story 1: Ghost in the Market
    story1 = Story(
        world_id=world.id,
        title="Ghost in the Market",
        synopsis="A memory broker discovers they've been selling fragments of their own erased past "
                 "and must reconstruct their identity while corporate hunters close in.",
        theme="identity, memory, commodification, redemption",
        status=StoryStatus.DRAFT,
        mode=AuthoringMode.AUTONOMOUS,
        pov_type=POVType.THIRD
    )
    session.add(story1)
    await session.flush()

    # Create minimal beats for story 1
    beat_story1 = StoryBeat(
        story_id=story1.id,
        content="The memory market in Sub-Level 7 never sleeps. Haze sits in the corner booth, "
               "neural jack exposed, waiting for customers. Tonight, someone buys a memory of sunset "
               "over mountains Haze doesn't remember ever seeing. The credit transfer is clean, "
               "but a fragment lingers: a name whispered in the memory's background noise. "
               "Their own name, from a voice they should recognize.",
        summary="Haze, a memory broker, sells a memory and catches a glimpse of their erased past.",
        local_time_label="2217, December 3rd, 23:47",
        type=BeatType.SCENE,
        order_index=1,
        generated_by=GeneratedBy.USER
    )
    session.add(beat_story1)

    await session.flush()
    print(f"  ✓ Created story: {story1.title} (1 beat)")

    return world


async def seed_demo_data():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("  SHINKEI DEMO DATA SEEDER")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # Create demo user
            user = await create_demo_user(session)

            # Create demo worlds
            await create_twilight_archive(session, user.id)
            await create_neon_babylon(session, user.id)

            # Commit all changes
            await session.commit()

            print("\n" + "=" * 60)
            print("  ✅ SEEDING COMPLETE!")
            print("=" * 60)
            print("\n📝 Demo Account Credentials:")
            print("   Email: demo@shinkei.app")
            print("   Password: (none - dev mode)")
            print("\n🌍 Worlds Created:")
            print("   1. The Twilight Archive (fragmented chronology)")
            print("   2. Neon Babylon (linear chronology)")
            print("\n📖 Stories Created:")
            print("   - The Archivist's Awakening (3 beats)")
            print("   - The Lost Cataloger (2 beats)")
            print("   - Ghost in the Market (1 beat)")
            print("\n🔗 World Events:")
            print("   - 9 total events across both worlds")
            print("   - Stories intersect at key timeline moments")
            print("\n✨ Ready for testing!")
            print("=" * 60 + "\n")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error seeding data: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
