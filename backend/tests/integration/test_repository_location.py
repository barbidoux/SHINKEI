"""Integration tests for Location repository."""
import pytest
from shinkei.repositories.user import UserRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.location import LocationRepository
from shinkei.schemas.user import UserCreate
from shinkei.schemas.world import WorldCreate
from shinkei.schemas.location import LocationCreate, LocationUpdate


@pytest.mark.asyncio
async def test_location_crud(session):
    """Test Location CRUD operations."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    loc_repo = LocationRepository(session)

    # Create User and World
    user = await user_repo.create(UserCreate(email="loc_test@example.com", name="LocTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Fantasy Realm", chronology_mode="linear"))

    # Create Location
    loc_data = LocationCreate(
        name="Rivendell",
        description="<p>Last Homely House</p>",
        location_type="city",
        significance="<p>Elven refuge</p>",
        coordinates={"lat": 45.0, "lng": -120.0},
        custom_metadata={"population": 500, "ruler": "Elrond"}
    )
    location = await loc_repo.create(world.id, loc_data)

    assert location.id is not None
    assert location.world_id == world.id
    assert location.name == "Rivendell"
    assert location.location_type == "city"
    assert location.coordinates["lat"] == 45.0
    assert location.custom_metadata["ruler"] == "Elrond"

    # Get by ID
    fetched_loc = await loc_repo.get_by_id(location.id)
    assert fetched_loc is not None
    assert fetched_loc.id == location.id

    # Get by World and ID
    fetched_loc_world = await loc_repo.get_by_world_and_id(world.id, location.id)
    assert fetched_loc_world is not None

    # List by World
    locations, total = await loc_repo.list_by_world(world.id)
    assert total == 1
    assert len(locations) == 1
    assert locations[0].id == location.id

    # Update
    update_data = LocationUpdate(
        description="<p>The Last Homely House East of the Sea</p>",
        significance="<p>Major Elven stronghold</p>"
    )
    updated_loc = await loc_repo.update(location.id, update_data)
    assert "East of the Sea" in updated_loc.description

    # Delete
    deleted = await loc_repo.delete(location.id)
    assert deleted is True

    # Verify Deletion
    deleted_loc = await loc_repo.get_by_id(location.id)
    assert deleted_loc is None


@pytest.mark.asyncio
async def test_location_hierarchy(session):
    """Test hierarchical location relationships."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    loc_repo = LocationRepository(session)

    user = await user_repo.create(UserCreate(email="loc_hierarchy@example.com", name="HierarchyTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Middle Earth", chronology_mode="linear"))

    # Create parent location
    middle_earth = await loc_repo.create(
        world.id,
        LocationCreate(name="Middle-earth", location_type="continent")
    )

    # Create child location
    shire = await loc_repo.create(
        world.id,
        LocationCreate(
            name="The Shire",
            location_type="region",
            parent_location_id=middle_earth.id
        )
    )

    # Create grandchild location
    hobbiton = await loc_repo.create(
        world.id,
        LocationCreate(
            name="Hobbiton",
            location_type="village",
            parent_location_id=shire.id
        )
    )

    # Get root locations
    roots = await loc_repo.get_root_locations(world.id)
    assert len(roots) == 1
    assert roots[0].id == middle_earth.id

    # Get children
    shire_children = await loc_repo.get_children(shire.id)
    assert len(shire_children) == 1
    assert shire_children[0].id == hobbiton.id

    # Get with hierarchy
    shire_with_hierarchy = await loc_repo.get_with_hierarchy(shire.id)
    assert shire_with_hierarchy is not None
    assert shire_with_hierarchy.parent_location_id == middle_earth.id


@pytest.mark.asyncio
async def test_location_circular_parent_prevention(session):
    """Test prevention of circular parent relationships."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    loc_repo = LocationRepository(session)

    user = await user_repo.create(UserCreate(email="loc_circular@example.com", name="CircularTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))

    # Create two locations
    loc_a = await loc_repo.create(world.id, LocationCreate(name="Location A", location_type="region"))
    loc_b = await loc_repo.create(
        world.id,
        LocationCreate(name="Location B", location_type="city", parent_location_id=loc_a.id)
    )

    # Try to create circular reference (B is child of A, try to make A child of B)
    with pytest.raises(ValueError, match="would create circular parent relationship"):
        await loc_repo.update(loc_a.id, LocationUpdate(parent_location_id=loc_b.id))


@pytest.mark.asyncio
async def test_location_filters(session):
    """Test location filtering."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    loc_repo = LocationRepository(session)

    user = await user_repo.create(UserCreate(email="loc_filter@example.com", name="FilterTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Fantasy World", chronology_mode="linear"))

    # Create parent
    continent = await loc_repo.create(
        world.id,
        LocationCreate(name="Continent", location_type="continent")
    )

    # Create children with different types
    await loc_repo.create(world.id, LocationCreate(name="City One", location_type="city", parent_location_id=continent.id))
    await loc_repo.create(world.id, LocationCreate(name="City Two", location_type="city", parent_location_id=continent.id))
    await loc_repo.create(world.id, LocationCreate(name="Forest", location_type="forest", parent_location_id=continent.id))

    # Filter by type
    cities, cities_total = await loc_repo.list_by_world(world.id, location_type="city")
    assert cities_total == 2

    forests, forests_total = await loc_repo.list_by_world(world.id, location_type="forest")
    assert forests_total == 1

    # Filter by parent
    children, children_total = await loc_repo.list_by_world(world.id, parent_location_id=continent.id)
    assert children_total == 3

    # Get root locations only
    roots, roots_total = await loc_repo.list_by_world(world.id, parent_location_id="null")
    assert roots_total == 1

    # Search
    search_results, search_total = await loc_repo.list_by_world(world.id, search="city one")
    assert search_total == 1
    assert search_results[0].name == "City One"


@pytest.mark.asyncio
async def test_location_with_mention_count(session):
    """Test getting location with mention count."""
    user_repo = UserRepository(session)
    world_repo = WorldRepository(session)
    loc_repo = LocationRepository(session)

    user = await user_repo.create(UserCreate(email="loc_mentions@example.com", name="MentionTester", password_hash="hashed_pw"))
    world = await world_repo.create(user.id, WorldCreate(name="Test World", chronology_mode="linear"))
    location = await loc_repo.create(world.id, LocationCreate(name="Castle", location_type="building"))

    # Location with no mentions
    result = await loc_repo.get_with_mention_count(location.id)
    assert result is not None
    loc_obj, mention_count = result
    assert loc_obj.id == location.id
    assert mention_count == 0
