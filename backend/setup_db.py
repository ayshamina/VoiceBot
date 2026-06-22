#!/usr/bin/env python
"""
Quick setup script for PostgreSQL and initial database configuration.
Run this after installing PostgreSQL and creating the voicebot user/database.
"""
import os
import sys
from pathlib import Path

def check_postgresql():
    """Check if PostgreSQL is installed and accessible."""
    try:
        import psycopg2
        print("[OK] psycopg2 is installed")
        return True
    except ImportError:
        print("[ERROR] psycopg2 not found. Install with: pip install psycopg2-binary")
        return False

def check_database_connection():
    """Test connection to PostgreSQL database."""
    try:
        from app.core.database import engine
        with engine.connect() as conn:
            print("[OK] Database connection successful!")
            return True
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify PostgreSQL is running")
        print("2. Check DATABASE_URL in .env file")
        print("3. Ensure voicebot user and database exist:")
        print("   psql -U postgres -c 'CREATE USER voicebot WITH PASSWORD \"voicebot\";'")
        print("   psql -U postgres -c 'CREATE DATABASE voicebot_db OWNER voicebot;'")
        return False

def initialize_database():
    """Initialize database tables and sample data."""
    try:
        from app.core.init_db import init_db, init_sample_data
        print("\nInitializing database...")
        init_db()
        print("[OK] Database tables created")
        
        init_sample_data()
        print("[OK] Sample data loaded")
        return True
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return False

def main():
    """Run the complete setup."""
    print("=" * 60)
    print("PostgreSQL Setup for Bridgeon VoiceBot")
    print("=" * 60)
    
    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    sys.path.insert(0, str(backend_dir))
    
    # Check for .env file
    if not Path(".env").exists():
        print("\n[ERROR] .env file not found!")
        print("  Copy .env.example to .env and update DATABASE_URL if needed")
        print(f"  cp .env.example .env")
        return False
    
    print("[OK] .env file found")
    
    # Check psycopg2
    if not check_postgresql():
        return False
    
    # Test database connection
    print("\nTesting database connection...")
    if not check_database_connection():
        return False
    
    # Initialize database
    if not initialize_database():
        return False
    
    print("\n" + "=" * 60)
    print("[OK] Setup complete! You can now start the backend:")
    print("  python main.py")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
