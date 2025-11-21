"""Reset database and seed with demo data."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from shinkei.database.engine import AsyncSessionLocal, engine
from seed_demo_data import seed_demo_data


async def reset_database():
    """Drop all tables and recreate them."""
    print("\n" + "=" * 80)
    print("  ⚠️  ⚠️  ⚠️   DANGER: DATABASE RESET WARNING   ⚠️  ⚠️  ⚠️")
    print("=" * 80)
    print("\n🔥 This will PERMANENTLY DELETE ALL DATA from the database!")
    print("   - All users will be deleted")
    print("   - All worlds will be deleted")
    print("   - All stories will be deleted")
    print("   - All story beats will be deleted")
    print("   - This action CANNOT be undone!")
    print("\n⚠️  Make sure you have a database backup before proceeding!")
    print("\n" + "=" * 80)

    # SAFETY CHECK #1: Require explicit confirmation
    confirmation = input("\n❓ Type 'DELETE ALL DATA' (in all caps) to confirm: ")
    if confirmation != "DELETE ALL DATA":
        print("\n✅ Reset cancelled. Database is safe.")
        sys.exit(0)

    # SAFETY CHECK #2: Second confirmation
    final_confirmation = input("\n❓ Are you ABSOLUTELY sure? Type 'YES I AM SURE': ")
    if final_confirmation != "YES I AM SURE":
        print("\n✅ Reset cancelled. Database is safe.")
        sys.exit(0)

    # SAFETY CHECK #3: Show what will be deleted
    print("\n📊 Checking current database state...")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
            result = await conn.execute(text("SELECT COUNT(*) FROM worlds"))
            world_count = result.scalar()
            result = await conn.execute(text("SELECT COUNT(*) FROM stories"))
            story_count = result.scalar()
            result = await conn.execute(text("SELECT COUNT(*) FROM story_beats"))
            beat_count = result.scalar()

        print(f"\n📈 Data that will be DELETED:")
        print(f"   - {user_count} users")
        print(f"   - {world_count} worlds")
        print(f"   - {story_count} stories")
        print(f"   - {beat_count} story beats")

        if user_count > 0 or world_count > 0:
            last_chance = input(f"\n❓ Delete all this data? Type 'YES' to proceed: ")
            if last_chance != "YES":
                print("\n✅ Reset cancelled. Database is safe.")
                sys.exit(0)
    except Exception as e:
        print(f"⚠️  Could not check database state: {e}")

    print("\n🗑️  Proceeding with database reset...")

    async with engine.begin() as conn:
        # Drop all tables in reverse dependency order
        await conn.execute(text("DROP TABLE IF EXISTS story_beats CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS world_events CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS stories CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS worlds CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))

    print("✓ All tables dropped")

    print("\n🔨 Running migrations to recreate schema...")
    import subprocess
    result = subprocess.run(
        ["poetry", "run", "alembic", "upgrade", "head"],
        cwd=Path(__file__).parent.parent,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ Database schema recreated")
    else:
        print(f"❌ Migration failed: {result.stderr}")
        sys.exit(1)


async def main():
    """Main reset and seed function."""
    try:
        # Reset database
        await reset_database()

        # Seed demo data
        await seed_demo_data()

        print("\n🎉 Database reset and seeded successfully!\n")

    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
