"""Integration tests for CharacterRelationship repository."""
import pytest
from shinkei.repositories.user import UserRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.character_relationship import CharacterRelationshipRepository
from shinkei.schemas.user import UserCreate
from shinkei.schemas.world import WorldCreate
from shinkei.schemas.character import CharacterCreate
from shinkei.schemas.character_relationship import CharacterRelationshipCreate, CharacterRelationshipUpdate


@pytest.mark.asyncio
async def test_character_relationship_crud(session):
    """Test CharacterRelationship CRUD operations."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    rel_repo = CharacterRelationshipRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="rel_test@example.com", name="RelTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    aragorn = await char_repo.create(world.id, CharacterCreate(name="Aragorn", importance="major"))
    arwen = await char_repo.create(world.id, CharacterCreate(name="Arwen", importance="major"))

    # Create Relationship
    rel_data = CharacterRelationshipCreate(
        character_a_id=aragorn.id,
        character_b_id=arwen.id,
        relationship_type="romantic",
        description="Destined lovers",
        strength="strong"
    )
    relationship = await rel_repo.create(world.id, rel_data)

    assert relationship.id is not None
    assert relationship.world_id == world.id
    assert relationship.character_a_id == aragorn.id
    assert relationship.character_b_id == arwen.id
    assert relationship.relationship_type == "romantic"
    assert relationship.strength.value == "strong"

    # Get by ID
    fetched_rel = await rel_repo.get_by_id(relationship.id)
    assert fetched_rel is not None
    assert fetched_rel.id == relationship.id

    # Get by World and ID
    fetched_rel_world = await rel_repo.get_by_world_and_id(world.id, relationship.id)
    assert fetched_rel_world is not None

    # List by World
    relationships, total = await rel_repo.list_by_world(world.id)
    assert total == 1
    assert len(relationships) == 1
    assert relationships[0].id == relationship.id

    # Update
    update_data = CharacterRelationshipUpdate(
        description="Star-crossed lovers united",
        strength="strong"
    )
    updated_rel = await rel_repo.update(relationship.id, update_data)
    assert "united" in updated_rel.description

    # Delete
    deleted = await rel_repo.delete(relationship.id)
    assert deleted is True

    # Verify Deletion
    deleted_rel = await rel_repo.get_by_id(relationship.id)
    assert deleted_rel is None


@pytest.mark.asyncio
async def test_character_relationship_filters(session):
    """Test relationship filtering."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    rel_repo = CharacterRelationshipRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="rel_filter@example.com", name="FilterTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Fellowship", chronology_mode="linear"))

    frodo = await char_repo.create(world.id, CharacterCreate(name="Frodo", importance="major"))
    sam = await char_repo.create(world.id, CharacterCreate(name="Sam", importance="major"))
    gandalf = await char_repo.create(world.id, CharacterCreate(name="Gandalf", importance="major"))
    saruman = await char_repo.create(world.id, CharacterCreate(name="Saruman", importance="major"))

    # Create relationships
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=frodo.id,
        character_b_id=sam.id,
        relationship_type="friendship",
        strength="strong"
    ))
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=gandalf.id,
        character_b_id=saruman.id,
        relationship_type="rivalry",
        strength="strong"
    ))
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=frodo.id,
        character_b_id=gandalf.id,
        relationship_type="mentorship",
        strength="moderate"
    ))

    # Filter by strength
    strong_rels, strong_total = await rel_repo.list_by_world(world.id, strength="strong")
    assert strong_total == 2

    moderate_rels, moderate_total = await rel_repo.list_by_world(world.id, strength="moderate")
    assert moderate_total == 1

    # Filter by relationship type
    friendship_rels, friendship_total = await rel_repo.list_by_world(
        world.id,
        relationship_type="friendship"
    )
    assert friendship_total == 1


@pytest.mark.asyncio
async def test_list_by_character(session):
    """Test getting all relationships for a character."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    rel_repo = CharacterRelationshipRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="char_rels@example.com", name="CharRelsTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))

    hero = await char_repo.create(world.id, CharacterCreate(name="Hero", importance="major"))
    friend = await char_repo.create(world.id, CharacterCreate(name="Friend", importance="major"))
    rival = await char_repo.create(world.id, CharacterCreate(name="Rival", importance="major"))
    mentor = await char_repo.create(world.id, CharacterCreate(name="Mentor", importance="major"))

    # Create relationships where hero is character_a
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=hero.id,
        character_b_id=friend.id,
        relationship_type="friendship",
        strength="strong"
    ))
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=hero.id,
        character_b_id=rival.id,
        relationship_type="rivalry",
        strength="moderate"
    ))

    # Create relationship where hero is character_b
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=mentor.id,
        character_b_id=hero.id,
        relationship_type="mentorship",
        strength="strong"
    ))

    # Get all relationships for hero
    hero_relationships = await rel_repo.list_by_character(hero.id)

    # Hero should have 3 relationships (2 as character_a, 1 as character_b)
    assert len(hero_relationships) == 3


@pytest.mark.asyncio
async def test_relationship_network_data(session):
    """Test getting network graph data."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    rel_repo = CharacterRelationshipRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="network@example.com", name="NetworkTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))

    char1 = await char_repo.create(world.id, CharacterCreate(name="Alice", importance="major"))
    char2 = await char_repo.create(world.id, CharacterCreate(name="Bob", importance="major"))
    char3 = await char_repo.create(world.id, CharacterCreate(name="Charlie", importance="minor"))

    # Create relationships
    rel1 = await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=char1.id,
        character_b_id=char2.id,
        relationship_type="friendship",
        strength="strong"
    ))
    rel2 = await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=char2.id,
        character_b_id=char3.id,
        relationship_type="acquaintance",
        strength="weak"
    ))

    # Get network data
    network_data = await rel_repo.get_network_data(world.id)

    assert "nodes" in network_data
    assert "edges" in network_data
    assert "total_characters" in network_data
    assert "total_relationships" in network_data

    assert network_data["total_characters"] == 3
    assert network_data["total_relationships"] == 2

    # Verify nodes
    nodes = network_data["nodes"]
    assert len(nodes) == 3
    node_ids = {node["id"] for node in nodes}
    assert char1.id in node_ids
    assert char2.id in node_ids
    assert char3.id in node_ids

    # Verify edges
    edges = network_data["edges"]
    assert len(edges) == 2


@pytest.mark.asyncio
async def test_unique_relationship_constraint(session):
    """Test that duplicate relationships are prevented."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    rel_repo = CharacterRelationshipRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="unique@example.com", name="UniqueTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))

    char_a = await char_repo.create(world.id, CharacterCreate(name="CharA", importance="major"))
    char_b = await char_repo.create(world.id, CharacterCreate(name="CharB", importance="major"))

    # Create first relationship
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=char_a.id,
        character_b_id=char_b.id,
        relationship_type="friendship",
        strength="strong"
    ))

    # Try to create duplicate relationship with same type
    # This should raise an IntegrityError due to unique constraint
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        await rel_repo.create(world.id, CharacterRelationshipCreate(
            character_a_id=char_a.id,
            character_b_id=char_b.id,
            relationship_type="friendship",
            strength="moderate"
        ))
        await session.commit()


@pytest.mark.asyncio
async def test_bidirectional_relationships(session):
    """Test that relationships work bidirectionally."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    char_repo = CharacterRepository(session)
    rel_repo = CharacterRelationshipRepository(session)

    # Setup
    user = await user_repo.create(UserCreate(email="bidir@example.com", name="BidirTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))

    alice = await char_repo.create(world.id, CharacterCreate(name="Alice", importance="major"))
    bob = await char_repo.create(world.id, CharacterCreate(name="Bob", importance="major"))

    # Create relationship A->B
    await rel_repo.create(world.id, CharacterRelationshipCreate(
        character_a_id=alice.id,
        character_b_id=bob.id,
        relationship_type="friendship",
        strength="strong"
    ))

    # Both characters should see the relationship
    alice_rels = await rel_repo.list_by_character(alice.id)
    bob_rels = await rel_repo.list_by_character(bob.id)

    assert len(alice_rels) == 1
    assert len(bob_rels) == 1
    assert alice_rels[0].id == bob_rels[0].id
