#!/usr/bin/env python3
"""
Automatic Database Backup Script

Creates timestamped backups of the PostgreSQL database.
Keeps the last 30 days of backups and deletes older ones.

Usage:
    python backup_database.py              # Create backup
    python backup_database.py --restore    # Restore latest backup
    python backup_database.py --list       # List all backups
"""
import asyncio
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shinkei.config import settings

# Backup configuration
BACKUP_DIR = Path(__file__).parent.parent / "backups"
BACKUP_RETENTION_DAYS = 30


def get_db_connection_string():
    """Extract database connection details from DATABASE_URL."""
    db_url = str(settings.database_url)

    # Parse postgresql://user:pass@host:port/dbname
    if "postgresql://" in db_url or "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")

        if "@" in db_url:
            auth, host_db = db_url.split("@")
            user, password = auth.split(":")
            host_port_db = host_db.split("/")
            host_port = host_port_db[0]
            dbname = host_port_db[1] if len(host_port_db) > 1 else "shinkei"

            if ":" in host_port:
                host, port = host_port.split(":")
            else:
                host, port = host_port, "5432"

            return {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "dbname": dbname
            }

    # Default values for development
    return {
        "host": "localhost",
        "port": "5432",
        "user": "shinkei_user",
        "password": "shinkei_pass_dev_only",
        "dbname": "shinkei"
    }


def create_backup():
    """Create a timestamped database backup."""
    # Ensure backup directory exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"shinkei_backup_{timestamp}.sql"

    print(f"\n📦 Creating database backup...")
    print(f"   Location: {backup_file}")

    # Get database connection details
    db_config = get_db_connection_string()

    # Create backup using pg_dump
    env = {
        "PGPASSWORD": db_config["password"]
    }

    cmd = [
        "pg_dump",
        "-h", db_config["host"],
        "-p", db_config["port"],
        "-U", db_config["user"],
        "-d", db_config["dbname"],
        "-f", str(backup_file),
        "--no-owner",
        "--no-acl",
        "--clean",
        "--if-exists"
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )

        file_size = backup_file.stat().st_size / 1024  # KB
        print(f"✅ Backup created successfully! ({file_size:.1f} KB)")

        # Clean up old backups
        cleanup_old_backups()

        return backup_file

    except subprocess.CalledProcessError as e:
        print(f"❌ Backup failed: {e.stderr}")
        if backup_file.exists():
            backup_file.unlink()
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: pg_dump not found. Is PostgreSQL client installed?")
        print("   Install with: apt-get install postgresql-client (Debian/Ubuntu)")
        print("                  brew install postgresql (macOS)")
        sys.exit(1)


def cleanup_old_backups():
    """Delete backups older than BACKUP_RETENTION_DAYS."""
    if not BACKUP_DIR.exists():
        return

    cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
    deleted_count = 0

    for backup_file in BACKUP_DIR.glob("shinkei_backup_*.sql"):
        # Extract timestamp from filename
        try:
            timestamp_str = backup_file.stem.replace("shinkei_backup_", "")
            file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

            if file_date < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
        except (ValueError, IndexError):
            pass  # Skip malformed filenames

    if deleted_count > 0:
        print(f"🗑️  Deleted {deleted_count} old backup(s) (older than {BACKUP_RETENTION_DAYS} days)")


def list_backups():
    """List all available backups."""
    if not BACKUP_DIR.exists() or not any(BACKUP_DIR.glob("shinkei_backup_*.sql")):
        print("📭 No backups found.")
        return

    print(f"\n📚 Available backups (in {BACKUP_DIR}):\n")

    backups = sorted(BACKUP_DIR.glob("shinkei_backup_*.sql"), reverse=True)

    for idx, backup_file in enumerate(backups, 1):
        timestamp_str = backup_file.stem.replace("shinkei_backup_", "")
        try:
            file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_date = file_date.strftime("%Y-%m-%d %H:%M:%S")
            file_size = backup_file.stat().st_size / 1024  # KB
            age_days = (datetime.now() - file_date).days

            print(f"  {idx}. {formatted_date} - {file_size:.1f} KB - {age_days} day(s) old")
        except ValueError:
            print(f"  {idx}. {backup_file.name}")

    print()


def restore_backup(backup_file: Path = None):
    """Restore database from backup."""
    if not BACKUP_DIR.exists():
        print("❌ No backup directory found.")
        sys.exit(1)

    # If no backup specified, use the latest
    if backup_file is None:
        backups = sorted(BACKUP_DIR.glob("shinkei_backup_*.sql"), reverse=True)
        if not backups:
            print("❌ No backups found to restore.")
            sys.exit(1)
        backup_file = backups[0]

    if not backup_file.exists():
        print(f"❌ Backup file not found: {backup_file}")
        sys.exit(1)

    print(f"\n⚠️  ⚠️  ⚠️  DATABASE RESTORE WARNING  ⚠️  ⚠️  ⚠️")
    print(f"\nThis will REPLACE ALL current data with backup from:")
    print(f"   {backup_file.name}")
    print(f"\n⚠️  Current database contents will be LOST!")

    confirmation = input("\n❓ Type 'RESTORE' to confirm: ")
    if confirmation != "RESTORE":
        print("✅ Restore cancelled.")
        sys.exit(0)

    print(f"\n♻️  Restoring database from backup...")

    # Get database connection details
    db_config = get_db_connection_string()

    env = {
        "PGPASSWORD": db_config["password"]
    }

    cmd = [
        "psql",
        "-h", db_config["host"],
        "-p", db_config["port"],
        "-U", db_config["user"],
        "-d", db_config["dbname"],
        "-f", str(backup_file)
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )

        print("✅ Database restored successfully!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Restore failed: {e.stderr}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database backup and restore utility")
    parser.add_argument("--restore", action="store_true", help="Restore latest backup")
    parser.add_argument("--list", action="store_true", help="List all backups")
    parser.add_argument("--backup-file", type=str, help="Specific backup file to restore")

    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.restore:
        backup_file = Path(args.backup_file) if args.backup_file else None
        restore_backup(backup_file)
    else:
        create_backup()


if __name__ == "__main__":
    main()
