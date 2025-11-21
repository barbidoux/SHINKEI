# 🛡️ Database Safety Guide

**CRITICAL: Read this before running ANY database commands!**

---

## ⚠️ What Happened (Data Loss Incident - Nov 21, 2025)

**A user lost ALL their worlds data** due to two bugs:

1. **Auto-Registration Bug**: The `/auth/login` endpoint was automatically creating NEW user accounts instead of rejecting unknown emails
2. **Unprotected Reset Script**: The `reset_and_seed.py` script had no safety checks and could be accidentally run

**Result**: User logged in after a database reset, got a brand new empty account, and couldn't access their original data.

---

## ✅ Safety Measures Now in Place

### 1. Fixed Auto-Registration Bug
- ❌ **OLD**: `/auth/login` auto-created accounts for unknown emails
- ✅ **NEW**: `/auth/login` now REJECTS unknown emails
- ✅ **NEW**: Use `/auth/register` endpoint to create new accounts

### 2. Protected Reset Script
The `backend/scripts/reset_and_seed.py` script now requires:
- ✅ Type "DELETE ALL DATA" to confirm
- ✅ Type "YES I AM SURE" for second confirmation
- ✅ Shows exactly what will be deleted (user count, world count, etc.)
- ✅ Final "YES" confirmation before deletion

### 3. Automatic Daily Backups
- ✅ Backup service runs daily at 2 AM UTC
- ✅ Keeps last 30 days of backups
- ✅ Backups stored in `backend/backups/`
- ✅ Manual backup: `python backend/scripts/backup_database.py`

### 4. Backup Commands
```bash
# Create manual backup
python backend/scripts/backup_database.py

# List all backups
python backend/scripts/backup_database.py --list

# Restore latest backup
python backend/scripts/backup_database.py --restore

# Restore specific backup
python backend/scripts/backup_database.py --restore --backup-file backups/shinkei_backup_20251121_090000.sql
```

---

## 🔥 DANGEROUS Commands (DATA LOSS RISK)

### ❌ NEVER RUN THESE WITHOUT BACKUPS:

```bash
# 🔥 DELETES ALL DATA - Requires 3 confirmations
python backend/scripts/reset_and_seed.py

# 🔥 DESTROYS DATABASE VOLUME - Permanent data loss!
docker-compose down -v

# 🔥 DELETES SPECIFIC VOLUME
docker volume rm docker_postgres_data

# 🔥 DROPS ALL TABLES
docker exec shinkei-postgres psql -U shinkei_user -d shinkei -c "DROP SCHEMA public CASCADE;"

# 🔥 MIGRATION DOWNGRADE - Can lose data
cd backend && poetry run alembic downgrade -1
```

### ⚠️ USE WITH CAUTION:

```bash
# Restarts containers (safe if volumes preserved)
docker-compose restart

# Rebuilds containers (safe if volumes preserved)
docker-compose up --build

# Stops containers (safe)
docker-compose down
```

---

## 📋 Safe Database Operations

### Create a Backup Before ANY Risky Operation:

```bash
# Step 1: ALWAYS create backup first
python backend/scripts/backup_database.py

# Step 2: Verify backup was created
ls -lh backend/backups/

# Step 3: NOW you can proceed with risky operation
```

### Check Current Database State:

```bash
# Count records in each table
docker exec shinkei-backend poetry run python -c "
import asyncio
from sqlalchemy import text
from shinkei.database.engine import engine

async def check():
    async with engine.begin() as conn:
        for table in ['users', 'worlds', 'stories', 'story_beats']:
            result = await conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
            print(f'{table}: {result.scalar()}')

asyncio.run(check())
"
```

### List All Backups:

```bash
python backend/scripts/backup_database.py --list
```

### Restore From Backup:

```bash
# Restore latest backup
python backend/scripts/backup_database.py --restore

# List backups first to choose specific one
python backend/scripts/backup_database.py --list

# Restore specific backup
python backend/scripts/backup_database.py --restore --backup-file backend/backups/shinkei_backup_20251121_120000.sql
```

---

## 🚨 Data Loss Recovery Checklist

If you lose data, follow these steps:

### 1. **STOP IMMEDIATELY**
- Don't run any more commands
- Don't restart containers
- Don't run migrations

### 2. **Check for Backups**
```bash
# List available backups
ls -lh backend/backups/

# Or use the script
python backend/scripts/backup_database.py --list
```

### 3. **Check Docker Volumes**
```bash
# List all volumes (look for orphaned postgres volumes)
docker volume ls

# Inspect specific volume
docker volume inspect docker_postgres_data
```

### 4. **Restore From Backup**
```bash
# Restore latest backup
python backend/scripts/backup_database.py --restore
```

### 5. **Verify Restoration**
```bash
# Check data counts
docker exec shinkei-backend poetry run python -c "
import asyncio
from sqlalchemy import text
from shinkei.database.engine import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT COUNT(*) FROM users'))
        print(f'Users: {result.scalar()}')
        result = await conn.execute(text('SELECT COUNT(*) FROM worlds'))
        print(f'Worlds: {result.scalar()}')

asyncio.run(check())
"
```

---

## 📝 Best Practices

### Development Workflow:

1. **Start of day**: Create a backup
   ```bash
   python backend/scripts/backup_database.py
   ```

2. **Before migrations**: Create a backup
   ```bash
   python backend/scripts/backup_database.py
   cd backend && poetry run alembic upgrade head
   ```

3. **Before testing reset script**: Create a backup
   ```bash
   python backend/scripts/backup_database.py
   python backend/scripts/reset_and_seed.py
   ```

4. **End of day**: Verify backup exists
   ```bash
   ls -lh backend/backups/ | tail -5
   ```

### Production Workflow:

1. **Always use migrations** (never reset_and_seed.py)
2. **Backup before every deployment**
3. **Test migrations on staging first**
4. **Keep 30+ days of backups**
5. **Store backups in off-site location** (S3, Google Cloud Storage, etc.)

---

## 🔧 Fixed Authentication Flow

### OLD (BROKEN) Flow:
1. User tries to login with `matthias.vaytet@gmail.com`
2. System checks database → not found
3. ❌ **BUG**: System creates NEW account automatically
4. User gets NEW empty account, loses access to old data

### NEW (FIXED) Flow:
1. User tries to login with `matthias.vaytet@gmail.com`
2. System checks database → not found
3. ✅ **FIXED**: System rejects login with error message
4. User must use `/auth/register` to create account explicitly

### Registration Flow:
```bash
# Register new account
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "dev",
    "name": "User Name"
  }'

# Login with existing account
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "dev"
  }'
```

---

## 📊 Backup Service Status

Check if automatic backups are working:

```bash
# View backup service logs
docker logs shinkei-backup --tail 50

# Check latest backup
ls -lth backend/backups/ | head -5

# Verify backup service is running
docker ps | grep shinkei-backup
```

---

## 🆘 Emergency Contacts

If you need help recovering data:

1. **Check GitHub Issues**: https://github.com/anthropics/shinkei/issues
2. **PostgreSQL Documentation**: https://www.postgresql.org/docs/current/backup.html
3. **Docker Volume Recovery**: https://docs.docker.com/storage/volumes/

---

## 📚 Additional Resources

- [PostgreSQL Backup Best Practices](https://www.postgresql.org/docs/current/backup.html)
- [Docker Volume Management](https://docs.docker.com/storage/volumes/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/en/latest/tutorial.html)

---

**Last Updated**: 2025-11-21
**Author**: Emergency Response Team
**Incident**: Data Loss Prevention Update
