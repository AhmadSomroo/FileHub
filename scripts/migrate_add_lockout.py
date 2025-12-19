#!/usr/bin/env python3
"""
Migration script to add brute force protection fields to User table
Run this once to update your existing database
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add new columns if they don't exist
        with db.engine.connect() as conn:
            # Check if columns exist
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'failed_login_attempts' not in columns:
                print("Adding failed_login_attempts column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
                conn.commit()
                print("✓ Added failed_login_attempts column")
            else:
                print("✓ failed_login_attempts column already exists")
            
            if 'locked_until' not in columns:
                print("Adding locked_until column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN locked_until DATETIME"))
                conn.commit()
                print("✓ Added locked_until column")
            else:
                print("✓ locked_until column already exists")
        
        print("\n✅ Migration completed successfully!")
        print("Your database now has brute force protection enabled.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("If you're starting fresh, you can delete data.db and restart the app.")
