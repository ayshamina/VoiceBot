# PostgreSQL Setup Guide for VoiceBot

This guide explains how to set up PostgreSQL for the Bridgeon Voice Call Assistant.

## Prerequisites

- **PostgreSQL 12+** installed and running
- Python 3.10+ with your virtual environment activated

## Step 1: Install PostgreSQL

### Windows
1. Download PostgreSQL installer from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Run the installer and follow the setup wizard
3. Remember the **superuser password** you set during installation (default username: `postgres`)
4. Ensure PostgreSQL service is running

### macOS
```bash
brew install postgresql@15
brew services start postgresql@15
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## Step 2: Create Database User and Database

Open a terminal and connect to PostgreSQL:

```bash
psql -U postgres
```

Then run these SQL commands:

```sql
-- Create the voicebot user
CREATE USER voicebot WITH PASSWORD 'voicebot';

-- Create the database
CREATE DATABASE voicebot_db OWNER voicebot;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE voicebot_db TO voicebot;

-- Exit
\q
```

## Step 3: Configure Your Backend

1. Copy the `.env.example` file to `.env`:
```bash
cp backend/.env.example backend/.env
```

2. Update `backend/.env` with your PostgreSQL credentials (if different from defaults):
```env
DATABASE_URL=postgresql://voicebot:voicebot@localhost:5432/voicebot_db
DATABASE_ECHO=false
```

## Step 4: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `sqlalchemy>=2.0.0` - ORM for database
- `psycopg2-binary>=2.9.0` - PostgreSQL driver
- `alembic>=1.13.0` - Database migrations (optional)

## Step 5: Verify Database Connection

Test the connection with:

```bash
python -c "from app.core.database import engine; engine.connect(); print('✓ Database connection successful!')"
```

## Step 6: Start the Backend

The database tables will be created automatically on first startup:

```bash
python main.py
```

You should see:
```
[DB] Initializing database...
[DB] All tables created successfully.
[INIT] Loaded X sample FAQ entries into knowledge base.
[DB] Database initialized successfully!
```

## What Changed

### New Files
- `app/core/database.py` - SQLAlchemy engine and session management
- `app/core/models.py` - Database models (Knowledge, Lead, Call, AuditLog, Setting, Event)
- `app/core/init_db.py` - Database initialization and sample data loading

### Updated Files
- `app/core/config.py` - Added DATABASE_URL and DATABASE_ECHO settings
- `app/core/call_store.py` - Converted to database-backed
- `app/core/settings_store.py` - Converted to database-backed
- `app/core/metrics.py` - Converted to database-backed
- `app/api/v1/endpoints/knowledge.py` - Converted to database-backed
- `app/api/v1/endpoints/leads.py` - Converted to database-backed
- `requirements.txt` - Added SQLAlchemy, psycopg2-binary, alembic

### Deprecated
- In-memory storage (`_KNOWLEDGE_DB`, `_LEADS_DB`, `_CALL_LOGS`, etc.)
- These are now persisted in PostgreSQL

## Database Schema

The following tables are automatically created:

### `knowledge` table
Stores FAQ/knowledge base entries with bilingual support
- Columns: id, question_en, answer_en, question_ml, answer_ml, category, created_at, updated_at

### `leads` table
Stores captured leads with consent tracking
- Columns: id, name, phone, course, consent_whatsapp, language, source, created_at

### `calls` table
Logs all voice calls and interactions
- Columns: id, call_id, caller_number, duration_seconds, language, outcome, metadata, timestamp

### `audit_logs` table
Tracks all admin actions and system events
- Columns: id, action, actor, target, details, timestamp

### `settings` table
Stores admin-controlled bot configuration
- Columns: id, key, value, updated_at

### `events` table
Tracks all bot interactions and analytics events
- Columns: id, event_type, entity_type, entity_id, data, timestamp

## API Changes

All API endpoints now require a database session. They use FastAPI's dependency injection:

```python
async def endpoint(db: Session = Depends(get_db)):
    # Use db for queries
    results = db.query(Model).all()
```

## Troubleshooting

### "Connection refused" error
- Check if PostgreSQL is running: `pg_isready -h localhost`
- Verify DATABASE_URL in `.env` is correct

### "User or password invalid"
- Verify PostgreSQL user credentials match `.env`
- Check if user exists: `psql -U postgres -c "\du"`

### "Database does not exist"
- Run the SQL commands in Step 2 again
- Verify database ownership: `psql -U postgres -c "\l"`

### "psycopg2" import error
- Reinstall: `pip install --force-reinstall psycopg2-binary`

## Data Migration (Optional)

If you have existing data from the in-memory version:

1. Export the old data (if applicable)
2. Restart the backend - it will create the database with sample data
3. Add any custom knowledge entries through the API

## Performance Tips

- Connection pooling is enabled by default (`pool_size=10`)
- Set `DATABASE_ECHO=true` in `.env` to see generated SQL (useful for debugging)
- Create indexes on frequently searched columns:
  ```sql
  CREATE INDEX idx_calls_timestamp ON calls(timestamp DESC);
  CREATE INDEX idx_leads_phone ON leads(phone);
  ```

## Next Steps

- Test the API: `curl http://localhost:8000/api/v1/health`
- Access API documentation: `http://localhost:8000/docs`
- Create knowledge entries through the dashboard
- Capture test leads through the bot simulator
