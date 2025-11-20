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
    print("\n" + "=" * 60)
    print("  ⚠️  DATABASE RESET WARNING")
    print("=" * 60)
    print("\nThis will DELETE ALL DATA from the database!")
    print("This action cannot be undone.")

    # In a script context, just proceed
    # In interactive mode, you might want to add: input("\nPress Enter to continue or Ctrl+C to cancel...")

    print("\n🗑️  Dropping all tables...")

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
