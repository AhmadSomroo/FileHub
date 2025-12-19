#!/usr/bin/env python3
"""
Migration script to add is_active column to users table
Run this once to update your existing database
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Add new column if it doesn't exist
        with db.engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'is_active' not in columns:
                print("Adding is_active column...")
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
                print("✓ Added is_active column")
                
                # Set all existing users to active
                conn.execute(text("UPDATE users SET is_active = 1 WHERE is_active IS NULL"))
                conn.commit()
                print("✓ Set all existing users to active")
            else:
                print("✓ is_active column already exists")
        
        print("\n✅ Migration completed successfully!")
        print("Admin can now:")
        print("  - Deactivate user accounts")
        print("  - Reactivate user accounts")
        print("  - Reset user passwords")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("If you're starting fresh, you can delete data.db and restart the app.")
